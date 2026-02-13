extern crate winresource;

fn main() {
    if cfg!(target_os = "windows") {
        #[cfg(not(debug_assertions))]
        let suffix = "";
        #[cfg(debug_assertions)]
        let suffix = "-dev";

        let product_name = format!("StarRailTools{}", suffix);
        let description = format!(
            "{}{}",
            std::env::var("CARGO_PKG_DESCRIPTION").unwrap(),
            suffix
        );

        winresource::WindowsResource::new()
            .set_icon("../assets/srt.ico")
            .set("ProductName", &product_name)
            .set("FileDescription", &description)
            .compile()
            .unwrap();
    }
}
