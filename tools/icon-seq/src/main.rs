//! The app icon's band drawn in, as the splash does it: 121 frames of
//! `app_icon_at` from progress 0 to 1, written as icon-000.png … icon-120.png.

use nus_render::icon::{app_icon_at, png};
use nus_render::theme::{signal, Theme};

fn main() {
    let dir = std::env::args().nth(1).unwrap_or_else(|| "out".into());
    std::fs::create_dir_all(&dir).unwrap();
    let ink = Theme::paper().ink;
    let size = 1024;
    for i in 0..=120u32 {
        let rgba = app_icon_at(size, ink, signal::RED, i as f32 / 120.0);
        std::fs::write(format!("{dir}/icon-{i:03}.png"), png(&rgba, size, size)).unwrap();
    }
    println!("wrote 121 frames to {dir}");
}
