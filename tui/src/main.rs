mod action;
mod app;
mod component;
mod events;
mod notification;
mod task;
mod worker;

/// 确保程序只有一个实例在运行
fn ensure_single_instance() {
    use std::sync::atomic::{AtomicIsize, Ordering};

    static MUTEX_HANDLE: AtomicIsize = AtomicIsize::new(0);

    const ERROR_ALREADY_EXISTS: u32 = 183;

    #[link(name = "kernel32")]
    unsafe extern "system" {
        fn CreateMutexW(
            lp_mutex_attributes: *const core::ffi::c_void,
            b_initial_owner: i32,
            lp_name: *const u16,
        ) -> isize;
        fn GetLastError() -> u32;
    }

    let name: Vec<u16> = "Global\\StarRailTools_SingleInstance\0"
        .encode_utf16()
        .collect();

    let handle = unsafe { CreateMutexW(core::ptr::null(), 1, name.as_ptr()) };

    if handle == 0 {
        // CreateMutexW 失败
        return;
    }

    if unsafe { GetLastError() } == ERROR_ALREADY_EXISTS {
        eprintln!("Application is already running.");
        std::process::exit(1);
    }

    MUTEX_HANDLE.store(handle, Ordering::Relaxed);
}

use app::App;
use srt::{APP_PATH, Result, logger};

#[tokio::main]
async fn main() -> Result<()> {
    ensure_single_instance();
    APP_PATH.init()?;
    logger::init(&APP_PATH.log_dir, Some(logger::Level::INFO))?;
    srt::DatabaseService::init()?;
    let mut app = App::new();
    app.init().await?;

    let mut terminal = ratatui::init();
    let result = app.run(&mut terminal).await;

    ratatui::restore();

    if let Err(ref e) = result {
        logger::error!("App run error: {:?}", e);

        eprintln!("{}\n{:#?}", i18n::I18nKey::UnknownError, e);
    }

    result
}
