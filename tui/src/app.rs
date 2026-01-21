use std::collections::HashMap;
use std::ops::{Deref, DerefMut};

use crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::{
    DefaultTerminal, Frame,
    layout::{Constraint, Layout},
    widgets::{ListState, Widget},
};
use tokio::sync::mpsc::{self, UnboundedReceiver, UnboundedSender};

use srt::{
    Result,
    core::{
        Account, AccountService, AppStateService, GachaAnalysisEntity, GachaAnalysisResult,
        GachaService, GachaType, Metadata, MetadataService,
    },
    logger,
};

use super::action::{AccountAction, Action, GachaAction, MetadataAction, RouteRequest, TaskAction};
use crate::component::{Footer, HomeWidget};
use crate::events::{Event, EventListener};
use crate::notification::{Notification, NotificationManager, NotificationType};
use crate::task::{TaskGroupId, TaskManager, TaskStatus};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FocusNode {
    // level 0
    Home,
    // Setting,
    // Help,

    // level 1
    AccountList,
    UpdateMenu,
    // DataMenu,

    // level 2
    AddAccount,
    DeleteAccount,
}

#[derive(Default)]
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
pub struct AppModel {
    pub focus_path: FocusPath,

    pub uid: Option<String>,

    pub uid_list: Vec<String>,
    pub uid_list_index: ListState,

    pub gacha_analysis: GachaAnalysisResult,
    /// gacha type array 顺序的索引
    pub gacha_type_index: usize,

    pub metadata: Metadata,
    pub metadata_updated: bool,
}

impl AppModel {
    pub fn new() -> Self {
        let mut state = AppModel::default();

        state.focus_path.push(FocusNode::Home);
        if !state.uid_list.is_empty() {
            state.uid_list_index.select(Some(0));
        }
        state
    }
}

pub struct App {
    exit: bool,

    model: AppModel,
    home_widget: HomeWidget,

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
        self.model.metadata = MetadataService::load_metadata().await?;
        if let Some(uid) = uid {
            self.model.gacha_analysis = GachaService::load_analysis(&uid).await?;
        }
        // TODO 加载配置 设置语言
        Ok(())
    }

    fn start_task(&mut self) -> Result<()> {
        // TODO 检查新版本
        self.task_manager.start(
            "sync_metadata",
            TaskGroupId::Global,
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
                ..
            } => {
                self.go_to_root(FocusNode::Home);
                return None;
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
            | FocusNode::UpdateMenu => self
                .home_widget
                .handle_key_event(key, &self.model.focus_path),
            // FocusNode::Setting => None,
            // FocusNode::Help => None,
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
            Action::Metadata(m) => self.handle_metadata_action(m),
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
            RouteRequest::OpenAccountListWidget => {
                self.model.focus_path.push(FocusNode::AccountList)
            }
            RouteRequest::OpenAddAccountWidget => self.model.focus_path.push(FocusNode::AddAccount),
            RouteRequest::OpenDeleteAccountWidget => {
                self.model.focus_path.push(FocusNode::DeleteAccount)
            }
            RouteRequest::OpenUpdateDataWidget => self.model.focus_path.push(FocusNode::UpdateMenu),
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
                let next = if current + 1 >= len { 0 } else { current + 1 };
                self.model.uid_list_index.select(Some(next));
            }
            AccountAction::SelectPrev => {
                let len = self.model.uid_list.len();
                if len == 0 {
                    self.model.uid_list_index.select(None);
                    return;
                }

                let current = self.model.uid_list_index.selected().unwrap_or(0);
                let prev = if current == 0 { len - 1 } else { current - 1 };
                self.model.uid_list_index.select(Some(prev));
            }
            AccountAction::StartAdd(uid) => {
                self.task_manager.start(
                    "register_account",
                    TaskGroupId::Global,
                    register_account(self.action_tx.clone(), uid),
                );
                self.model.focus_path.pop();
            }
            AccountAction::AddSuccess(uid) => {
                self.notify(&format!("账户 {} 添加成功", uid), NotificationType::Info);
                self.model.uid_list.push(uid);
                self.model.uid_list_index.select(Some(0));
                self.model.uid_list.sort();
            }
            AccountAction::StartDelete => {
                if let Some(idx) = self.model.uid_list_index.selected() {
                    self.task_manager.start(
                        "delete_account",
                        TaskGroupId::User,
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

                    self.notify(&format!("账户 {} 删除成功", uid), NotificationType::Info);

                    if Some(uid) == self.model.uid {
                        self.task_manager.cancel_group(TaskGroupId::User);
                        self.model.uid = None;
                        self.model.gacha_analysis = GachaAnalysisResult::default();
                    }

                    if self.model.uid_list.is_empty() {
                        self.model.uid_list_index.select(None);
                    } else {
                        self.model.uid_list_index.select(Some(0));
                    }
                }
            }
            AccountAction::StartLogin => {
                self.model.focus_path.pop();

                if let Some(idx) = self.model.uid_list_index.selected() {
                    if let Some(uid) = self.model.uid_list.get(idx) {
                        self.task_manager.cancel_group(TaskGroupId::User);

                        self.task_manager.start(
                            "set_default_account",
                            TaskGroupId::Global,
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
                    load_analysis(self.action_tx.clone(), uid),
                );
            }
        }
    }

    fn handle_gacha_action(&mut self, gacha_action: GachaAction) {
        match gacha_action {
            GachaAction::NextTab => {
                self.model.gacha_type_index = (self.model.gacha_type_index + 1) % 6;
            }
            GachaAction::PrevTab => {
                self.model.gacha_type_index = (self.model.gacha_type_index + 5) % 6;
            }
            GachaAction::AnalysisLoaded(analysis) => {
                self.model.gacha_analysis = analysis;
            }
            GachaAction::StartRefresh(fetch_all) => {
                if let Some(uid) = self.model.uid.clone() {
                    self.task_manager.start(
                        "refresh_gacha_records",
                        TaskGroupId::User,
                        refresh_gacha_records(self.action_tx.clone(), uid, fetch_all),
                    );
                }
                self.model.focus_path.pop();
            }
            GachaAction::RefreshSuccess(count) => {
                self.notify(&format!("更新了 {} 条记录", count), NotificationType::Info);
            }
        }
    }

    fn handle_metadata_action(&mut self, metadata_action: MetadataAction) {
        match metadata_action {
            MetadataAction::Synced => {
                self.task_manager.start(
                    "load_metadata",
                    TaskGroupId::Global,
                    reload_metadata(self.action_tx.clone()),
                );
            }

            MetadataAction::Reloaded(metadata) => {
                self.model.metadata = metadata;
                self.model.metadata_updated = true;
            }
        }
    }

    fn handle_task_action(&mut self, task_action: TaskAction) {
        match task_action {
            TaskAction::Failed(_, error) => {
                // TODO 区分类型发送不同级别的通知
                self.notify(i18n::loc(error.msg.key), NotificationType::Error);
            }
            TaskAction::Cancelled(_task_id) => {
                if let Some(task) = self.task_manager.get_task(_task_id) {
                    task.status = TaskStatus::Cancelled;
                }
            }
            TaskAction::Started(_task_id) => {}
            TaskAction::Completed(_task_id) => {
                if let Some(task) = self.task_manager.get_task(_task_id) {
                    task.status = TaskStatus::Completed;
                }
            }
        }
    }
}

// =========================================================================
// 异步任务
// =========================================================================

async fn sync_metadata(tx: UnboundedSender<Action>) -> Result<()> {
    MetadataService::sync_metadata().await?;
    let _ = tx.send(Action::Metadata(MetadataAction::Synced));
    Ok(())
}

async fn reload_metadata(tx: UnboundedSender<Action>) -> Result<()> {
    let metadata = MetadataService::load_metadata().await?;
    let _ = tx.send(Action::Metadata(MetadataAction::Reloaded(metadata)));
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
