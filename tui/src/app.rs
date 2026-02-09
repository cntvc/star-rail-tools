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

use srt::{
    APP_PATH, AppConfig, Result,
    core::{
        AccountService, AppStateService, GachaAnalysisResult, GachaService, Metadata,
        MetadataService,
    },
    logger, updater,
};

use super::action::{
    AccountAction, Action, ExportAction, GachaAction, ImportAction, MetadataAction, RouteRequest,
    SettingAction, TaskAction,
};
use crate::component::{Footer, HelpWidget, HomeWidget, SPINNERS, SettingWidget};
use crate::events::{Event, EventListener};
use crate::notification::{Notification, NotificationManager, NotificationType};
use crate::task::{TaskGroupId, TaskId, TaskManager, TaskStatus};

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
    About,

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
    pub metadata_is_updated: bool,

    pub config: AppConfig,

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
    setting_widget: SettingWidget,

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
            setting_widget: SettingWidget::new(),
            event_tx,
            event_rx,
            action_tx,
            action_rx,
            event_listener: EventListener::new(),
            notification_manager: NotificationManager::new(),
            task_manager,
        }
    }

    pub async fn init(&mut self) -> Result<()> {
        let uid = AppStateService::get_default_uid().await?;
        self.model.uid = uid.clone();
        self.model.uid_list = AccountService::get_all_uid_list().await?;
        if !self.model.uid_list.is_empty() {
            self.model.uid_list_index.select(Some(0));
        }
        self.model.metadata = Arc::new(MetadataService::load_metadata().await?);

        self.model.config = AppConfig::load_config().await?;
        i18n::set_lang(self.model.config.language);

        if let Some(uid) = uid {
            self.model.gacha_analysis = GachaService::load_analysis(&uid).await?;
        }
        if self.model.gacha_analysis.is_empty() {
            self.model.home_mode = HomeMode::Welcome;
        } else {
            self.model.home_mode = HomeMode::Data;
        }
        Ok(())
    }

    fn start_task(&mut self) -> Result<()> {
        self.task_manager.start(
            "check_update",
            TaskGroupId::Global,
            true,
            i18n::loc(i18n::I18nKey::TaskCheckUpdate),
            check_update(self.action_tx.clone()),
        );

        self.task_manager.start(
            "sync_metadata",
            TaskGroupId::Global,
            true,
            i18n::loc(i18n::I18nKey::TaskSyncMetadata),
            sync_metadata(self.action_tx.clone()),
        );

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
                        self.update(action);
                    }
                }

                Some(action) = self.action_rx.recv() => {
                    self.update(action);
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
        let [main_area, footer_area] =
            Layout::vertical([Constraint::Fill(1), Constraint::Length(1)]).areas(area);

        let root_path = self.model.focus_path.root_path().unwrap();
        match root_path {
            FocusNode::Home => self.home_widget.render(&mut self.model, main_area, frame),
            FocusNode::Setting => self
                .setting_widget
                .render(&mut self.model, main_area, frame),
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
        logger::info!("route key: {:?}", key.code);
        // 全局快捷键
        match key {
            KeyEvent {
                code: KeyCode::Char('q'),
                modifiers: KeyModifiers::CONTROL,
                ..
            } => {
                return Some(Action::Quit);
            }
            KeyEvent {
                code: KeyCode::Char('h'),
                modifiers: KeyModifiers::NONE,
                ..
            } => {
                return Some(Action::Route(RouteRequest::SwitchToHome));
            }
            KeyEvent {
                code: KeyCode::Char('s'),
                modifiers: KeyModifiers::NONE,
                ..
            } => {
                return Some(Action::Route(RouteRequest::SwitchToSetting));
            }
            KeyEvent {
                code: KeyCode::Char('?') | KeyCode::Char('/'),
                modifiers: KeyModifiers::NONE,
                ..
            } => {
                return Some(Action::Route(RouteRequest::SwitchToHelp));
            }
            _ => {}
        }

        // 2. 根据 focus_path 末端分发
        let current_focus = self.model.focus_path.last().copied().unwrap();
        logger::info!("current focus: {:?}", current_focus);
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
            FocusNode::Setting | FocusNode::SettingSaveConfirm => self
                .setting_widget
                .handle_key_event(key, &self.model.focus_path),

            FocusNode::Help | FocusNode::About => self
                .help_widget
                .handle_key_event(key, &self.model.focus_path),
        }
    }

    fn update(&mut self, action: Action) {
        match action {
            Action::Quit => {
                self.exit = true;
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
            } => self.notify(&message, notification_type),
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
}

// =========================================================================
// 处理 Action
// =========================================================================
impl App {
    fn handle_route_action(&mut self, route: RouteRequest) {
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
                self.go_to_root(FocusNode::Setting);
                self.setting_widget.load_config(&self.model.config);
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
                    return;
                }

                self.model.focus_path.push(FocusNode::UpdateMenu)
            }
            RouteRequest::OpenImportExportMenu => {
                if self.model.uid.is_none() {
                    self.notify(
                        i18n::loc(i18n::I18nKey::NotifyPleaseLoginFirst),
                        NotificationType::Warning,
                    );
                    return;
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
            RouteRequest::OpenAbout => self.model.focus_path.push(FocusNode::About),
        }
    }

    fn handle_account_action(&mut self, account_action: AccountAction) {
        match account_action {
            AccountAction::SelectNext => {
                let len = self.model.uid_list.len();
                if len == 0 {
                    self.model.uid_list_index.select(None);
                    return;
                }

                let current = self.model.uid_list_index.selected().unwrap_or(len - 1);
                let next = (current + 1) % len;
                self.model.uid_list_index.select(Some(next));
            }
            AccountAction::SelectPrev => {
                let len = self.model.uid_list.len();
                if len == 0 {
                    self.model.uid_list_index.select(None);
                    return;
                }

                let current = self.model.uid_list_index.selected().unwrap_or(0);
                let prev = (current + len - 1) % len;
                self.model.uid_list_index.select(Some(prev));
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
            }
            AccountAction::AddSuccess(uid) => {
                self.notify(
                    i18n::loc(i18n::I18nKey::NotifyAccountAddedSuccessfully),
                    NotificationType::Info,
                );
                self.model.uid_list.push(uid);
                self.model.uid_list_index.select(Some(0));
                self.model.uid_list.sort();
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
            }
            AccountAction::Login => {
                self.model.focus_path.pop();

                if let Some(idx) = self.model.uid_list_index.selected() {
                    if let Some(uid) = self.model.uid_list.get(idx) {
                        self.task_manager.cancel_group(TaskGroupId::User);

                        self.task_manager.start(
                            "set_default_account",
                            TaskGroupId::Global,
                            false,
                            "set_default_account",
                            set_default_account(self.action_tx.clone(), uid.clone()),
                        );
                    }
                }
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
            }
        }
    }

    fn handle_gacha_action(&mut self, gacha_action: GachaAction) {
        match gacha_action {
            GachaAction::AnalysisLoaded(analysis) => {
                self.model.gacha_analysis = analysis;
                if self.model.gacha_analysis.is_empty() {
                    self.model.home_mode = HomeMode::Welcome;
                } else {
                    self.model.home_mode = HomeMode::Data;
                }
            }
            GachaAction::Refresh(fetch_all) => {
                if !self.model.metadata_is_updated {
                    self.notify(
                        i18n::loc(i18n::I18nKey::NotifyWaitForMetadataUpdate),
                        NotificationType::Warning,
                    );
                    return;
                }

                if let Some(uid) = self.model.uid.clone() {
                    self.task_manager.start(
                        "refresh_gacha_records",
                        TaskGroupId::User,
                        true,
                        i18n::loc(i18n::I18nKey::TaskRefreshGachaRecords),
                        refresh_gacha_records(self.action_tx.clone(), uid, fetch_all),
                    );
                }
                self.model.focus_path.pop();
            }
            GachaAction::RefreshSuccess(count) => {
                self.notify(
                    &i18n::loc(i18n::I18nKey::NotifyRecordsUpdated)
                        .replace("{0}", &count.to_string()),
                    NotificationType::Info,
                );
            }
        }
    }

    fn handle_import_action(&mut self, import_action: ImportAction) {
        match import_action {
            ImportAction::SelectNext => {
                if self.model.import_file_list.is_empty() {
                    return;
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
            }
            ImportAction::SelectPrev => {
                if self.model.import_file_list.is_empty() {
                    return;
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
            }
            ImportAction::ScanFile => {
                self.task_manager.start(
                    "scan_import_file_list",
                    TaskGroupId::User,
                    true,
                    i18n::loc(i18n::I18nKey::TaskScanImportFiles),
                    scan_import_file_list(self.action_tx.clone()),
                );
            }
            ImportAction::ScanFileSuccess(files) => {
                self.model.import_file_list = files;
                if !self.model.import_file_list.is_empty() {
                    self.model.import_file_list_index.select(Some(0));
                }
            }
            ImportAction::Import => {
                if !self.model.metadata_is_updated {
                    self.notify(
                        i18n::loc(i18n::I18nKey::NotifyWaitForMetadataUpdate),
                        NotificationType::Warning,
                    );
                    return;
                }

                if let Some(idx) = self.model.import_file_list_index.selected() {
                    if let Some(file_path) = self.model.import_file_list.get(idx) {
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
                }
            }
            ImportAction::ImportSuccess(count) => {
                self.notify(
                    &i18n::loc(i18n::I18nKey::NotifyImportSuccess)
                        .replace("{0}", &count.to_string()),
                    NotificationType::Info,
                );
                self.task_manager.start(
                    "load_analysis",
                    TaskGroupId::Global,
                    false,
                    "load_analysis",
                    load_analysis(self.action_tx.clone(), self.model.uid.clone().unwrap()),
                );
            }
        }
    }

    fn handle_export_action(&mut self, export_action: ExportAction) {
        match export_action {
            ExportAction::Export => {
                if self.model.uid.is_none() {
                    self.notify(
                        i18n::loc(i18n::I18nKey::NotifyPleaseLoginFirst),
                        NotificationType::Warning,
                    );
                    return;
                }
                self.task_manager.start(
                    "export_gacha_record",
                    TaskGroupId::User,
                    false,
                    "export_gacha_record",
                    export_gacha_record(
                        self.action_tx.clone(),
                        self.model.uid.clone().unwrap(),
                        self.model.config.language.clone(),
                        Arc::clone(&self.model.metadata),
                    ),
                );
            }
            ExportAction::ExportSuccess => {
                let path = APP_PATH.root_dir.join(&self.model.uid.clone().unwrap());
                self.notify(
                    &i18n::loc(i18n::I18nKey::NotifyExportSuccess)
                        .replace("{0}", &path.display().to_string()),
                    NotificationType::Info,
                );
            }
        }
    }

    fn handle_metadata_action(&mut self, metadata_action: MetadataAction) {
        match metadata_action {
            MetadataAction::SyncSuccess => {
                self.task_manager.start(
                    "load_metadata",
                    TaskGroupId::Global,
                    false,
                    "load_metadata",
                    reload_metadata(self.action_tx.clone()),
                );
            }
            MetadataAction::ReloadSuccess(metadata) => {
                self.model.metadata = Arc::new(metadata);
                self.model.metadata_is_updated = true;
            }
        }
    }

    fn handle_setting_action(&mut self, setting_action: SettingAction) {
        match setting_action {
            SettingAction::Save(config) => {
                self.model.config = config;
                self.task_manager.start(
                    "save_config",
                    TaskGroupId::Global,
                    false,
                    "save_config",
                    save_config(self.action_tx.clone(), self.model.config),
                );
            }
            SettingAction::SaveSuccess => {
                self.model.focus_path.pop();
            }
        }
    }

    fn handle_task_action(&mut self, task_action: TaskAction) {
        match task_action {
            TaskAction::Failed(task_id, error) => {
                let notification_type = match error.msg.key {
                    i18n::I18nKey::TaskExecutionFailed
                    | i18n::I18nKey::IoError
                    | i18n::I18nKey::TimeParseError
                    | i18n::I18nKey::DatabaseError => NotificationType::Error,
                    _ => NotificationType::Warning,
                };
                self.notify(i18n::loc(error.msg.key), notification_type);
                self.remove_visible_task(&task_id);

                if let Some(task) = self.task_manager.get_task(&task_id) {
                    task.status = TaskStatus::Failed;
                }

                if error.msg.key == i18n::I18nKey::DatabaseError {
                    self.exit = true;
                }
            }
            TaskAction::Cancelled(task_id) => {
                if let Some(task) = self.task_manager.get_task(&task_id) {
                    task.status = TaskStatus::Cancelled;
                }
                self.remove_visible_task(&task_id);
            }
            TaskAction::Started(task_id) => {
                if let Some(task) = self.task_manager.get_task(&task_id) {
                    if task.visible {
                        self.add_visible_task(task_id);
                    }
                }
            }
            TaskAction::Completed(task_id) => {
                if let Some(task) = self.task_manager.get_task(&task_id) {
                    task.status = TaskStatus::Completed;
                }
                self.remove_visible_task(&task_id);
            }
        }
    }
}

// =========================================================================
// 异步任务
// =========================================================================

async fn sync_metadata(tx: UnboundedSender<Action>) -> Result<()> {
    MetadataService::sync_metadata().await?;
    let _ = tx.send(Action::Metadata(MetadataAction::SyncSuccess));
    Ok(())
}

async fn reload_metadata(tx: UnboundedSender<Action>) -> Result<()> {
    let metadata = MetadataService::load_metadata().await?;
    let _ = tx.send(Action::Metadata(MetadataAction::ReloadSuccess(metadata)));
    Ok(())
}

async fn register_account(tx: UnboundedSender<Action>, uid: String) -> Result<()> {
    AccountService::register(&uid).await?;
    let _ = tx.send(Action::Account(AccountAction::AddSuccess(uid)));
    Ok(())
}

async fn load_analysis(tx: UnboundedSender<Action>, uid: String) -> Result<()> {
    let analysis = GachaService::load_analysis(&uid).await?;
    let _ = tx.send(Action::Gacha(GachaAction::AnalysisLoaded(analysis)));
    Ok(())
}

async fn set_default_account(tx: UnboundedSender<Action>, uid: String) -> Result<()> {
    AppStateService::set_default_uid(&uid).await?;
    let _ = tx.send(Action::Account(AccountAction::LoginSuccess(uid)));
    Ok(())
}

async fn unregister_account(tx: UnboundedSender<Action>, uid: String) -> Result<()> {
    AccountService::unregister(&uid).await?;
    let _ = tx.send(Action::Account(AccountAction::DeleteSuccess));
    Ok(())
}

async fn refresh_gacha_records(
    tx: UnboundedSender<Action>,
    uid: String,
    fetch_all: bool,
) -> Result<()> {
    let count = GachaService::refresh_gacha_record(&uid, fetch_all).await?;
    let _ = tx.send(Action::Gacha(GachaAction::RefreshSuccess(count)));
    let analysis = GachaService::update_analysis(&uid).await?;
    let _ = tx.send(Action::Gacha(GachaAction::AnalysisLoaded(analysis)));
    Ok(())
}

async fn save_config(tx: UnboundedSender<Action>, config: AppConfig) -> Result<()> {
    AppConfig::save_config(&config).await?;
    let _ = tx.send(Action::Setting(SettingAction::SaveSuccess));
    Ok(())
}

async fn check_update(tx: UnboundedSender<Action>) -> Result<()> {
    let latest_version = updater::get_latest_release_version().await?;
    let msg = match latest_version {
        Some(version) => format!("检测到新版本: {}", version),
        None => "当前已是最新版本".to_string(),
    };

    let _ = tx.send(Action::Notify {
        message: msg,
        notification_type: NotificationType::Info,
    });
    Ok(())
}

async fn scan_import_file_list(tx: UnboundedSender<Action>) -> Result<()> {
    let files = GachaService::get_json_file_list(&APP_PATH.import_dir).await?;
    let _ = tx.send(Action::Import(ImportAction::ScanFileSuccess(files)));
    Ok(())
}

async fn import_gacha_record(
    tx: UnboundedSender<Action>,
    uid: String,
    file_path: PathBuf,
    metadata: Arc<Metadata>,
) -> Result<()> {
    let count = GachaService::import_record(&uid, &file_path, metadata).await?;
    let _ = tx.send(Action::Import(ImportAction::ImportSuccess(count)));
    Ok(())
}

async fn export_gacha_record(
    tx: UnboundedSender<Action>,
    uid: String,
    lang: i18n::Lang,
    metadata: Arc<Metadata>,
) -> Result<()> {
    let export_dir = APP_PATH.root_dir.join(&uid);
    GachaService::export_to_uigf(&uid, &export_dir, lang, metadata).await?;
    let _ = tx.send(Action::Export(ExportAction::ExportSuccess));
    Ok(())
}
