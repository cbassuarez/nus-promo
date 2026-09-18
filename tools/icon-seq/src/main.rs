//! The app icon's band drawn in, as the splash does it: 121 frames of
//! `app_icon_at` from progress 0 to 1, for both faces — paper (an ink n, for
//! white grounds) as icon-000.png … and ink (a paper n, for black) under ink/.

use nus_render::icon::{app_icon_at, png};
use nus_render::theme::{signal, Theme};

fn main() {
    let dir = std::env::args().nth(1).unwrap_or_else(|| "out".into());
    for (sub, n) in [("", Theme::paper().ink), ("ink/", Theme::ink().ink)] {
        let out = format!("{dir}/{sub}");
        std::fs::create_dir_all(&out).unwrap();
        for i in 0..=120u32 {
            let rgba = app_icon_at(1024, n, signal::RED, i as f32 / 120.0);
            std::fs::write(format!("{out}icon-{i:03}.png"), png(&rgba, 1024, 1024)).unwrap();
        }
    }
    println!("wrote 2 × 121 frames to {dir}");
}
