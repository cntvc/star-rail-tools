extern crate winresource;

fn main() {
    if cfg!(target_os = "windows") {
        winresource::WindowsResource::new()
            .set_icon("assets/srt.ico")
            .set("ProductName", "StarRailTools")
            .set("FileDescription", "StarRailTools")
            .compile()
            .unwrap();
    }
}
