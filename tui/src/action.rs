use srt::AppError;
use srt::core::{GachaAnalysisResult, Metadata};

use crate::notification::NotificationType;
use crate::task::TaskId;

/// 应用业务动作 - 描述"发生了什么"

pub enum Action {
    Quit,

    Route(RouteRequest),

    Account(AccountAction),

    Gacha(GachaAction),

    Metadata(MetadataAction),

    Task(TaskAction),

    Notify {
        message: String,
        notification_type: NotificationType,
    },
}

pub enum RouteRequest {
    Close,
    OpenAccountListWidget,
    OpenAddAccountWidget,
    OpenDeleteAccountWidget,
    OpenUpdateDataWidget,
}

pub enum AccountAction {
    SelectNext,
    SelectPrev,
    StartLogin,
    LoginSuccess(String),
    StartAdd(String),
    AddSuccess(String),
    StartDelete,
    DeleteSuccess,
}

pub enum GachaAction {
    NextTab,
    PrevTab,
    StartRefresh(bool),
    RefreshSuccess(usize),
    AnalysisLoaded(GachaAnalysisResult),
}

pub enum TaskAction {
    Started(TaskId),
    Cancelled(TaskId),
    Completed(TaskId),
    Failed(TaskId, AppError),
}

pub enum MetadataAction {
    Synced,
    Reloaded(Metadata),
}
