use std::path::PathBuf;

use srt::core::{GachaAnalysisResult, Metadata};
use srt::{AppConfig, AppError};

use crate::notification::NotificationType;
use crate::task::TaskId;

pub enum Action {
    Quit,

    Route(RouteRequest),

    Account(AccountAction),

    Gacha(GachaAction),

    Import(ImportAction),

    Export(ExportAction),

    Metadata(MetadataAction),

    Setting(SettingAction),

    Task(TaskAction),

    Notify {
        message: String,
        notification_type: NotificationType,
    },
}

pub enum RouteRequest {
    Close,
    SwitchToHome,
    SwitchToSetting,
    SwitchToHelp,

    OpenAccountList,
    OpenAddAccount,
    OpenDeleteAccount,

    OpenUpdateGachaDataMenu,

    OpenImportExportMenu,
    OpenImportFileList,

    OpenSaveSettingConfirm,
    OpenAbout,
}

pub enum AccountAction {
    SelectNext,
    SelectPrev,
    Login,
    LoginSuccess(String),
    Add(String),
    AddSuccess(String),
    Delete,
    DeleteSuccess,
}

pub enum GachaAction {
    Refresh(bool),
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
    SyncSuccess,
    ReloadSuccess(Metadata),
}

pub enum SettingAction {
    SaveSuccess,
    Save(AppConfig),
}

pub enum ImportAction {
    SelectNext,
    SelectPrev,
    ScanFile,
    ScanFileSuccess(Vec<PathBuf>),
    Import,
    ImportSuccess(usize),
}

pub enum ExportAction {
    Export,
    ExportSuccess,
}
