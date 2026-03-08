use std::collections::VecDeque;
use std::ops::{Deref, DerefMut};
use std::path::PathBuf;
use std::sync::Arc;

use crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::{
    DefaultTerminal, Frame,
    layout::{Constraint, Layout},
    widgets::{ListState, Widget},
};
use tokio::sync::mpsc::{self, UnboundedReceiver, UnboundedSender};
use tracing::instrument;

use srt::{
    APP_PATH, AppConfig, ConfigItem, Result,
    core::{
        AccountService, AppStateItem, AppStateService, GachaAnalysisResult, GachaService, Metadata,
        MetadataService,
    },
    logger::{self, Level},
};

use super::action::{
    AccountAction, Action, ExportAction, GachaAction, ImportAction, MetadataAction, RouteRequest,
    SettingAction, TaskAction,
};
use super::worker::*;
use crate::component::{Footer, HelpWidget, HomeWidget, SPINNERS, SettingWidget};
use crate::events::{Event, EventListener};
use crate::notification::{Notification, NotificationManager, NotificationType};
use crate::task::{TaskGroupId, TaskId, TaskManager, TaskStatus};

const METADATA_SYNC_INTERVAL: i64 = 60 * 60 * 24 * 14;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FocusNode {
    // level 0
    Home,
    Setting,
    Help,

    // level 1
    AccountList,
    UpdateMenu,
    ImportExportMenu,
    SettingSaveConfirm,

    // level 2
    AddAccount,
    DeleteAccount,
    ImportFileList,
}

#[derive(Default, Debug)]
pub struct FocusPath {
    inner: Vec<FocusNode>,
}

impl Deref for FocusPath {
    type Target = Vec<FocusNode>;

    fn deref(&self) -> &Self::Target {
        &self.inner
    }
}

impl DerefMut for FocusPath {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.inner
    }
}

impl FocusPath {
    pub fn root_path(&self) -> Option<FocusNode> {
        self.inner.first().copied()
    }
}

#[derive(Default)]
pub enum HomeMode {
    #[default]
    Welcome,
    Data,
}

#[derive(Debug, Clone)]
pub struct VisibleTask {
    pub id: TaskId,
    pub description: String,
}

#[derive(Default)]
pub struct AppModel {
    pub focus_path: FocusPath,

    pub uid: Option<String>,

    pub uid_list: Vec<String>,
    pub uid_list_index: ListState,

    pub gacha_analysis: GachaAnalysisResult,

    pub home_mode: HomeMode,

    pub import_file_list: Vec<PathBuf>,
    pub import_file_list_index: ListState,

    pub metadata: Arc<Metadata>,
    pub latest_metadata_sync_utc_time: Option<i64>,

    pub config: AppConfig,
    pub temporary_config: AppConfig,
    pub config_item_index: usize,

    pub visible_tasks: VecDeque<VisibleTask>,
    pub spinner_index: usize,
}

impl AppModel {
    pub fn new() -> Self {
        let mut state = AppModel::default();

        state.focus_path.push(FocusNode::Home);
        state
    }
}

pub struct App {
    exit: bool,

    model: AppModel,
    home_widget: HomeWidget,
    help_widget: HelpWidget,

    event_tx: UnboundedSender<Event>,
    event_rx: UnboundedReceiver<Event>,
    action_tx: UnboundedSender<Action>,
    action_rx: UnboundedReceiver<Action>,

    event_listener: EventListener,
    notification_manager: NotificationManager,
    task_manager: TaskManager,
}

impl App {
    pub fn new() -> Self {
        let (event_tx, event_rx) = mpsc::unbounded_channel();
        let (action_tx, action_rx) = mpsc::unbounded_channel();
        let task_manager = TaskManager::new(action_tx.clone());

        Self {
            exit: false,
            model: AppModel::new(),
            home_widget: HomeWidget::new(),
            help_widget: HelpWidget::new(),
            event_tx,
            event_rx,
            action_tx,
            action_rx,
            event_listener: EventListener::new(),
            notification_manager: NotificationManager::new(),
            task_manager,
        }
    }

    #[instrument(level = "info", skip_all)]
    pub async fn init(&mut self) -> Result<()> {
        let uid = AppStateService::get::<String>(AppStateItem::DefaultAccount).await?;
        self.model.uid = uid.clone();
        self.model.uid_list = AccountService::get_all_uid_list().await?;
        if !self.model.uid_list.is_empty() {
            self.model.uid_list_index.select(Some(0));
        }
        self.model.metadata = Arc::new(MetadataService::load_metadata().await?);

        self.model.latest_metadata_sync_utc_time = MetadataService::get_latest_sync_time().await?;

        let config = AppConfig::load_config().await?;
        self.apply_config(config)?;

        if let Some(uid) = uid {
            self.model.gacha_analysis = GachaService::load_analysis(&uid).await?;
        }
        if self.model.gacha_analysis.is_empty() {
            self.model.home_mode = HomeMode::Welcome;
        } else {
            self.model.home_mode = HomeMode::Data;
        }

        logger::info!(
            "\nApp initialized\nUID: {:?}\nUID count: {}\nMetadata items: {}\nconfig: {:?}",
            self.model.uid,
            self.model.uid_list.len(),
            self.model.metadata.len(),
            self.model.config
        );

        Ok(())
    }

    fn start_task(&mut self) -> Result<()> {
        if self.model.config.check_update {
            self.task_manager.start(
                "check_update",
                TaskGroupId::Global,
                true,
                i18n::loc(i18n::I18nKey::TaskCheckUpdate),
                check_update(self.action_tx.clone()),
            );
        }

        let need_sync_metadata = {
            if let Some(last_sync_time) = self.model.latest_metadata_sync_utc_time {
                let now_utc_timestamp = time::OffsetDateTime::now_utc().unix_timestamp();
                now_utc_timestamp - last_sync_time > METADATA_SYNC_INTERVAL
            } else {
                // 首次启动时，强制同步
                true
            }
        };

        if need_sync_metadata {
            self.task_manager.start(
                "sync_metadata",
                TaskGroupId::Global,
                true,
                i18n::loc(i18n::I18nKey::TaskSyncMetadata),
                sync_metadata(self.action_tx.clone()),
            );
        }

        Ok(())
    }

    pub async fn run(&mut self, terminal: &mut DefaultTerminal) -> Result<()> {
        self.event_listener.start(self.event_tx.clone());
        self.start_task()?;

        loop {
            terminal.draw(|frame| self.draw(frame))?;

            tokio::select! {
                Some(event) = self.event_rx.recv() => {
                    if let Some(action) = self.handle_event(event) {
                        self.update(action)?;
                    }
                }

                Some(action) = self.action_rx.recv() => {
                    self.update(action)?;
                }
            }

            if self.exit {
                break;
            }
        }

        self.stop();
        Ok(())
    }

    fn draw(&mut self, frame: &mut Frame) {
        let area = frame.area();

        //  快速 resize 窗口大小时，可能导致值为 0，直接返回
        if area.width == 0 || area.height == 0 {
            return;
        }

        let [main_area, footer_area] =
            Layout::vertical([Constraint::Fill(1), Constraint::Length(1)]).areas(area);

        let root_path = self.model.focus_path.root_path().unwrap();
        match root_path {
            FocusNode::Home => self.home_widget.render(&mut self.model, main_area, frame),
            FocusNode::Setting => SettingWidget::render(&self.model, main_area, frame),
            FocusNode::Help => self.help_widget.render(&mut self.model, main_area, frame),
            _ => {}
        }

        self.notification_manager
            .render(main_area, frame.buffer_mut());

        Footer.render(&self.model, footer_area, frame.buffer_mut());
    }

    fn stop(&mut self) {
        self.task_manager.cancel_all();
        self.event_listener.stop();
    }

    // =========================================================================
    // 事件处理
    // =========================================================================

    fn handle_event(&mut self, event: Event) -> Option<Action> {
        match event {
            Event::Key(key) => self.route_key_event(key),
            Event::Tick => {
                self.notification_manager.remove_expired();
                self.task_manager.cleanup_finished();

                if !self.model.visible_tasks.is_empty() {
                    self.model.spinner_index = (self.model.spinner_index + 1) % SPINNERS.len();
                }
                None
            }
        }
    }

    fn route_key_event(&mut self, key: KeyEvent) -> Option<Action> {
        logger::trace!("route key: {:?}", key);
        // 全局快捷键
        if key.code == KeyCode::Char('q') && key.modifiers.contains(KeyModifiers::CONTROL) {
            return Some(Action::Quit);
        }

        // 2. 根据 focus_path 末端分发
        let current_focus = self.model.focus_path.last().copied().unwrap();

        match current_focus {
            FocusNode::Home
            | FocusNode::AccountList
            | FocusNode::AddAccount
            | FocusNode::DeleteAccount
            | FocusNode::UpdateMenu
            | FocusNode::ImportExportMenu
            | FocusNode::ImportFileList => self
                .home_widget
                .handle_key_event(key, &self.model.focus_path),
            FocusNode::Setting | FocusNode::SettingSaveConfirm => {
                SettingWidget::handle_key_event(key, &self.model.focus_path)
            }

            FocusNode::Help => self
                .help_widget
                .handle_key_event(key, &self.model.focus_path),
        }
    }

    fn update(&mut self, action: Action) -> Result<()> {
        match action {
            Action::Quit => {
                self.exit = true;
                Ok(())
            }

            Action::Route(r) => self.handle_route_action(r),
            Action::Account(a) => self.handle_account_action(a),
            Action::Gacha(g) => self.handle_gacha_action(g),
            Action::Import(i) => self.handle_import_action(i),
            Action::Export(e) => self.handle_export_action(e),
            Action::Metadata(m) => self.handle_metadata_action(m),
            Action::Setting(s) => self.handle_setting_action(s),
            Action::Task(t) => self.handle_task_action(t),
            Action::Notify {
                message,
                notification_type,
            } => {
                self.notify(&message, notification_type);
                Ok(())
            }
        }
    }

    // =========================================================================
    // 帮助函数
    // =========================================================================
    fn go_to_root(&mut self, focus_node: FocusNode) {
        self.model.focus_path.clear();
        self.model.focus_path.push(focus_node);
    }

    fn notify(&mut self, message: &str, notification_type: NotificationType) {
        self.notification_manager
            .add(Notification::new(message, notification_type));
    }

    fn reset_widgets(&mut self) {
        // 只有 home 状态需要重置
        self.home_widget = HomeWidget::new();
    }

    fn add_visible_task(&mut self, task_id: TaskId) {
        if let Some(task) = self.task_manager.get_task(&task_id) {
            self.model.visible_tasks.push_front(VisibleTask {
                id: task_id,
                description: task.description.clone(),
            });
        }
    }

    fn remove_visible_task(&mut self, task_id: &TaskId) {
        self.model.visible_tasks.retain(|task| &task.id != task_id);
        if self.model.visible_tasks.is_empty() {
            self.model.spinner_index = 0;
        }
    }

    fn apply_config(&mut self, config: AppConfig) -> Result<()> {
        self.model.config = config;
        i18n::set_lang(self.model.config.language);
        logger::update_level(self.model.config.log_level)?;
        Ok(())
    }
}

// =========================================================================
// 处理 Action
// =========================================================================

impl App {
    fn handle_route_action(&mut self, route: RouteRequest) -> Result<()> {
        match route {
            RouteRequest::Close => {
                if self.model.focus_path.len() > 1 {
                    self.model.focus_path.pop();
                }
            }
            RouteRequest::SwitchToHome => {
                self.go_to_root(FocusNode::Home);
            }
            RouteRequest::SwitchToSetting => {
                self.model.temporary_config = self.model.config;
                self.go_to_root(FocusNode::Setting);
            }
            RouteRequest::SwitchToHelp => {
                self.go_to_root(FocusNode::Help);
            }
            RouteRequest::OpenAccountList => self.model.focus_path.push(FocusNode::AccountList),
            RouteRequest::OpenAddAccount => self.model.focus_path.push(FocusNode::AddAccount),
            RouteRequest::OpenDeleteAccount => self.model.focus_path.push(FocusNode::DeleteAccount),
            RouteRequest::OpenUpdateGachaDataMenu => {
                if self.model.uid.is_none() {
                    self.notify(
                        i18n::loc(i18n::I18nKey::NotifyPleaseLoginFirst),
                        NotificationType::Warning,
                    );
                    return Ok(());
                }

                self.model.focus_path.push(FocusNode::UpdateMenu)
            }
            RouteRequest::OpenImportExportMenu => {
                if self.model.uid.is_none() {
                    self.notify(
                        i18n::loc(i18n::I18nKey::NotifyPleaseLoginFirst),
                        NotificationType::Warning,
                    );
                    return Ok(());
                }

                self.model.focus_path.push(FocusNode::ImportExportMenu)
            }
            RouteRequest::OpenImportFileList => {
                self.model.focus_path.push(FocusNode::ImportFileList);
                self.task_manager.start(
                    "scan_import_file_list",
                    TaskGroupId::User,
                    false,
                    "scan_import_file_list",
                    scan_import_file_list(self.action_tx.clone()),
                );
            }
            RouteRequest::OpenSaveSettingConfirm => {
                self.model.focus_path.push(FocusNode::SettingSaveConfirm)
            }
        }
        Ok(())
    }

    fn handle_account_action(&mut self, account_action: AccountAction) -> Result<()> {
        match account_action {
            AccountAction::SelectNext => {
                let len = self.model.uid_list.len();
                if len == 0 {
                    self.model.uid_list_index.select(None);
                    return Ok(());
                }

                let current = self.model.uid_list_index.selected().unwrap_or(len - 1);
                let next = (current + 1) % len;
                self.model.uid_list_index.select(Some(next));
                Ok(())
            }
            AccountAction::SelectPrev => {
                let len = self.model.uid_list.len();
                if len == 0 {
                    self.model.uid_list_index.select(None);
                    return Ok(());
                }

                let current = self.model.uid_list_index.selected().unwrap_or(0);
                let prev = (current + len - 1) % len;
                self.model.uid_list_index.select(Some(prev));
                Ok(())
            }
            AccountAction::Add(uid) => {
                self.task_manager.start(
                    "register_account",
                    TaskGroupId::Global,
                    false,
                    "register_account",
                    register_account(self.action_tx.clone(), uid),
                );
                self.model.focus_path.pop();
                Ok(())
            }
            AccountAction::AddSuccess(uid) => {
                self.notify(
                    i18n::loc(i18n::I18nKey::NotifyAccountAddedSuccessfully),
                    NotificationType::Info,
                );
                self.model.uid_list.push(uid);
                self.model.uid_list_index.select(Some(0));
                self.model.uid_list.sort();
                Ok(())
            }
            AccountAction::Delete => {
                if let Some(idx) = self.model.uid_list_index.selected() {
                    self.task_manager.start(
                        "delete_account",
                        TaskGroupId::User,
                        false,
                        "delete_account",
                        unregister_account(
                            self.action_tx.clone(),
                            self.model.uid_list[idx].clone(),
                        ),
                    );
                }
                self.model.focus_path.pop();
                Ok(())
            }
            AccountAction::DeleteSuccess => {
                if let Some(idx) = self.model.uid_list_index.selected() {
                    let uid = self.model.uid_list.remove(idx);

                    self.notify(
                        i18n::loc(i18n::I18nKey::NotifyAccountDeletedSuccessfully),
                        NotificationType::Info,
                    );

                    if Some(uid) == self.model.uid {
                        self.task_manager.cancel_group(TaskGroupId::User);
                        self.model.uid = None;
                        self.model.gacha_analysis = GachaAnalysisResult::default();
                        self.model.home_mode = HomeMode::Welcome;
                    }

                    if self.model.uid_list.is_empty() {
                        self.model.uid_list_index.select(None);
                    } else {
                        self.model.uid_list_index.select(Some(0));
                    }
                }
                Ok(())
            }
            AccountAction::Login => {
                self.model.focus_path.pop();

                if let Some(idx) = self.model.uid_list_index.selected()
                    && let Some(uid) = self.model.uid_list.get(idx)
                {
                    self.task_manager.cancel_group(TaskGroupId::User);

                    self.task_manager.start(
                        "set_default_account",
                        TaskGroupId::Global,
                        false,
                        "set_default_account",
                        set_default_account(self.action_tx.clone(), uid.clone()),
                    );
                }
                Ok(())
            }
            AccountAction::LoginSuccess(uid) => {
                self.model.uid = Some(uid.clone());
                self.task_manager.start(
                    "load_analysis",
                    TaskGroupId::Global,
                    false,
                    "load_analysis",
                    load_analysis(self.action_tx.clone(), uid),
                );
                self.reset_widgets();
                Ok(())
            }
        }
    }

    fn handle_gacha_action(&mut self, gacha_action: GachaAction) -> Result<()> {
        match gacha_action {
            GachaAction::AnalysisLoaded(analysis) => {
                self.model.gacha_analysis = analysis;
                if self.model.gacha_analysis.is_empty() {
                    self.model.home_mode = HomeMode::Welcome;
                } else {
                    self.model.home_mode = HomeMode::Data;
                }
                Ok(())
            }
            GachaAction::Refresh(fetch_all) => {
                if let Some(uid) = self.model.uid.clone() {
                    self.task_manager.start(
                        "refresh_gacha_records",
                        TaskGroupId::User,
                        true,
                        i18n::loc(i18n::I18nKey::TaskRefreshGachaRecords),
                        refresh_gacha_records(
                            self.action_tx.clone(),
                            uid,
                            fetch_all,
                            Arc::clone(&self.model.metadata),
                        ),
                    );
                }
                self.model.focus_path.pop();
                Ok(())
            }
            GachaAction::RefreshSuccess(count) => {
                self.notify(
                    &i18n::loc(i18n::I18nKey::NotifyRecordsUpdateSuccess)
                        .replace("{0}", &count.to_string()),
                    NotificationType::Info,
                );
                Ok(())
            }
        }
    }

    fn handle_import_action(&mut self, import_action: ImportAction) -> Result<()> {
        match import_action {
            ImportAction::SelectNext => {
                if self.model.import_file_list.is_empty() {
                    return Ok(());
                }
                match self.model.import_file_list_index.selected() {
                    None => {
                        self.model.import_file_list_index.select(Some(0));
                    }
                    Some(idx) => {
                        self.model
                            .import_file_list_index
                            .select(Some((idx + 1) % self.model.import_file_list.len()));
                    }
                }
                Ok(())
            }
            ImportAction::SelectPrev => {
                if self.model.import_file_list.is_empty() {
                    return Ok(());
                }
                match self.model.import_file_list_index.selected() {
                    None => {
                        self.model.import_file_list_index.select(Some(0));
                    }
                    Some(idx) => {
                        self.model.import_file_list_index.select(Some(
                            (idx + self.model.import_file_list.len() - 1)
                                % self.model.import_file_list.len(),
                        ));
                    }
                }
                Ok(())
            }
            ImportAction::ScanFile => {
                self.task_manager.start(
                    "scan_import_file_list",
                    TaskGroupId::User,
                    true,
                    i18n::loc(i18n::I18nKey::TaskScanImportFiles),
                    scan_import_file_list(self.action_tx.clone()),
                );
                Ok(())
            }
            ImportAction::ScanFileSuccess(files) => {
                self.model.import_file_list = files;
                if !self.model.import_file_list.is_empty() {
                    self.model.import_file_list_index.select(Some(0));
                }
                Ok(())
            }
            ImportAction::Import => {
                if let Some(idx) = self.model.import_file_list_index.selected()
                    && let Some(file_path) = self.model.import_file_list.get(idx)
                {
                    self.task_manager.start(
                        "import_gacha_record",
                        TaskGroupId::User,
                        false,
                        "import_gacha_record",
                        import_gacha_record(
                            self.action_tx.clone(),
                            self.model.uid.clone().unwrap(), // 这里必定有值，在进入前已进行判断
                            file_path.clone(),
                            Arc::clone(&self.model.metadata),
                        ),
                    );
                }
                Ok(())
            }
            ImportAction::ImportSuccess(count) => {
                if count > 0 {
                    self.notify(
                        &i18n::loc(i18n::I18nKey::NotifyRecordsUpdateSuccess)
                            .replace("{0}", &count.to_string()),
                        NotificationType::Info,
                    );
                } else {
                    self.notify(
                        i18n::loc(i18n::I18nKey::NotifyImportNoNewData),
                        NotificationType::Info,
                    );
                }

                Ok(())
            }
        }
    }

    fn handle_export_action(&mut self, export_action: ExportAction) -> Result<()> {
        match export_action {
            ExportAction::Export => {
                if self.model.uid.is_none() {
                    self.notify(
                        i18n::loc(i18n::I18nKey::NotifyPleaseLoginFirst),
                        NotificationType::Warning,
                    );
                    return Ok(());
                }
                self.task_manager.start(
                    "export_gacha_record",
                    TaskGroupId::User,
                    false,
                    "export_gacha_record",
                    export_gacha_record(
                        self.action_tx.clone(),
                        self.model.uid.clone().unwrap(),
                        self.model.config.language,
                        Arc::clone(&self.model.metadata),
                    ),
                );
                Ok(())
            }
            ExportAction::ExportSuccess => {
                let path = APP_PATH.root_dir.join(self.model.uid.clone().unwrap());
                self.notify(
                    &i18n::loc(i18n::I18nKey::NotifyExportSuccess)
                        .replace("{0}", &path.display().to_string()),
                    NotificationType::Info,
                );
                Ok(())
            }
        }
    }

    fn handle_metadata_action(&mut self, metadata_action: MetadataAction) -> Result<()> {
        match metadata_action {
            MetadataAction::SyncSuccess => {
                self.task_manager.start(
                    "load_metadata",
                    TaskGroupId::Global,
                    false,
                    "load_metadata",
                    reload_metadata(self.action_tx.clone()),
                );
                self.task_manager.start(
                    "update_sync_metadata_time",
                    TaskGroupId::Global,
                    false,
                    "",
                    update_sync_metadata_time(self.action_tx.clone()),
                );
                Ok(())
            }
            MetadataAction::UpdateSyncTimeSuccess(t) => {
                self.model.latest_metadata_sync_utc_time = Some(t);
                Ok(())
            }
            MetadataAction::ReloadSuccess(metadata) => {
                self.model.metadata = Arc::new(metadata);
                Ok(())
            }
        }
    }

    fn handle_setting_action(&mut self, setting_action: SettingAction) -> Result<()> {
        match setting_action {
            SettingAction::Select(item_increment) => {
                let config_array = ConfigItem::as_array();
                let config_len = config_array.len();

                if item_increment != 0 {
                    let mut new_idx =
                        self.model.config_item_index as isize + item_increment as isize;
                    new_idx =
                        (new_idx % config_len as isize + config_len as isize) % config_len as isize;
                    self.model.config_item_index = new_idx as usize;
                }
                Ok(())
            }
            SettingAction::Increment(value_increment) => {
                let config_array = ConfigItem::as_array();
                let current_item = config_array[self.model.config_item_index];
                match current_item {
                    ConfigItem::Language => {
                        self.model.temporary_config.language =
                            match self.model.temporary_config.language {
                                i18n::Lang::zh_cn => i18n::Lang::en_us,
                                i18n::Lang::en_us => i18n::Lang::zh_cn,
                            };
                    }
                    ConfigItem::CheckUpdate => {
                        self.model.temporary_config.check_update =
                            !self.model.temporary_config.check_update;
                    }
                    ConfigItem::LogLevel => {
                        let level = self.model.temporary_config.log_level;
                        self.model.temporary_config.log_level = if value_increment > 0 {
                            match level {
                                Level::TRACE => Level::DEBUG,
                                Level::DEBUG => Level::INFO,
                                Level::INFO => Level::WARN,
                                Level::WARN => Level::ERROR,
                                Level::ERROR => Level::DEBUG,
                            }
                        } else {
                            match level {
                                Level::TRACE => Level::ERROR,
                                Level::DEBUG => Level::TRACE,
                                Level::INFO => Level::DEBUG,
                                Level::WARN => Level::INFO,
                                Level::ERROR => Level::WARN,
                            }
                        };
                    }
                }
                Ok(())
            }
            SettingAction::Save => {
                self.task_manager.start(
                    "save_config",
                    TaskGroupId::Global,
                    false,
                    "save_config",
                    save_config(self.action_tx.clone(), self.model.temporary_config),
                );
                Ok(())
            }
            SettingAction::SaveSuccess(config) => {
                self.apply_config(config)?;
                self.model.focus_path.pop();
                Ok(())
            }
        }
    }

    fn handle_task_action(&mut self, task_action: TaskAction) -> Result<()> {
        match task_action {
            TaskAction::Failed(task_id, error) => {
                logger::error!("\nTask failed. ID: {}\n{:#?}", task_id, error);
                let notification_type = match error.kind {
                    i18n::I18nKey::TaskExecutionFailed
                    | i18n::I18nKey::IoError
                    | i18n::I18nKey::TimeParseError
                    | i18n::I18nKey::DatabaseError => NotificationType::Error,
                    _ => NotificationType::Warning,
                };
                self.notify(i18n::loc(error.kind), notification_type);
                self.remove_visible_task(&task_id);

                if let Some(task) = self.task_manager.get_task(&task_id) {
                    task.status = TaskStatus::Failed;
                }

                if error.kind == i18n::I18nKey::DatabaseError {
                    self.exit = true;
                }
                Ok(())
            }
            TaskAction::Cancelled(task_id) => {
                logger::info!("Task cancelled. ID: {}", task_id);
                if let Some(task) = self.task_manager.get_task(&task_id) {
                    task.status = TaskStatus::Cancelled;
                }
                self.remove_visible_task(&task_id);
                Ok(())
            }
            TaskAction::Started(task_id) => {
                logger::info!("Task started. ID: {}", task_id);
                if let Some(task) = self.task_manager.get_task(&task_id)
                    && task.visible
                {
                    self.add_visible_task(task_id);
                }
                Ok(())
            }
            TaskAction::Completed(task_id) => {
                logger::info!("Task completed. ID: {}", task_id);
                if let Some(task) = self.task_manager.get_task(&task_id) {
                    task.status = TaskStatus::Completed;
                }
                self.remove_visible_task(&task_id);
                Ok(())
            }
        }
    }
}
