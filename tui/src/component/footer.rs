use ratatui::{
    buffer::Buffer,
    layout::{Constraint, Layout, Rect},
    style::{Color, Style},
    text::{Line, Span},
    widgets::{Paragraph, Widget},
};
use unicode_width::UnicodeWidthStr;

use crate::app::{self, AppModel, FocusNode};
use i18n::I18nKey;

pub const SPINNERS: [&str; 10] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

pub struct Footer;

impl Footer {
    pub fn render(&self, app_model: &AppModel, area: Rect, buf: &mut Buffer) {
        // 背景色填充
        let bg_color = Color::Rgb(0, 119, 199); // #0077c7  
        for y in area.top()..area.bottom() {
            for x in area.left()..area.right() {
                buf[(x, y)].set_bg(bg_color);
            }
        }

        let global_menu_spans = self.build_global_menu_spans(app_model);
        let global_menu_width = self.calc_spans_width(&global_menu_spans);

        let uid_text = self.build_uid_text(app_model);

        let [global_area, middle_area, uid_area] = Layout::horizontal([
            Constraint::Length(global_menu_width),
            Constraint::Min(1),
            Constraint::Length(uid_text.width() as u16),
        ])
        .areas(area);

        self.render_spans(&global_menu_spans, global_area, buf);

        let uid_span = Span::styled(uid_text, Style::default().fg(Color::White));
        self.render_spans(&[uid_span], uid_area, buf);

        // 计算任务进度区域宽度
        let task_progress_width = if app_model.visible_tasks.is_empty() {
            0
        } else {
            // spinner(2) + 空格(1) + 描述文字 + 左右边距(2)
            let desc_len = app_model
                .visible_tasks
                .front()
                .map(|task| task.description.width())
                .unwrap_or(0);
            (desc_len + 4).min(30) as u16
        };

        let [shortcuts_area, task_area] =
            Layout::horizontal([Constraint::Min(1), Constraint::Length(task_progress_width)])
                .areas(middle_area);

        self.render_focus_shortcuts(app_model, shortcuts_area, buf);

        if task_progress_width > 0 {
            self.render_task_progress(app_model, task_area, buf);
        }
    }

    fn render_task_progress(&self, app_model: &AppModel, area: Rect, buf: &mut Buffer) {
        if let Some(task) = app_model.visible_tasks.front() {
            let spinner = SPINNERS[app_model.spinner_index];
            let text = format!(" {} {} ", task.description, spinner);

            let span = Span::styled(text, Style::default().fg(Color::White));
            self.render_spans(&[span], area, buf);
        }
    }

    fn build_global_menu_spans(&self, app_model: &AppModel) -> Vec<Span<'static>> {
        let current_root = app_model.focus_path.root_path();

        let style = Style::default().fg(Color::White);
        let highlight_style = Style::default().fg(Color::Rgb(255, 209, 102));
        let mut spans = Vec::new();

        let home_style = if current_root == Some(FocusNode::Home) {
            highlight_style
        } else {
            style
        };
        spans.push(Span::raw(" "));
        spans.push(Span::styled(
            i18n::loc(I18nKey::TuiFooterHomeMenu),
            home_style,
        ));

        let setting_style = if current_root == Some(FocusNode::Setting) {
            highlight_style
        } else {
            style
        };
        spans.push(Span::raw(" "));
        spans.push(Span::styled(
            i18n::loc(I18nKey::TuiFooterSettingMenu),
            setting_style,
        ));

        let help_style = if current_root == Some(FocusNode::Help) {
            highlight_style
        } else {
            style
        };
        spans.push(Span::raw(" "));
        spans.push(Span::styled(
            i18n::loc(I18nKey::TuiFooterHelpMenu),
            help_style,
        ));

        spans
    }

    fn build_uid_text(&self, app_model: &AppModel) -> String {
        if let Some(uid) = &app_model.uid {
            format!(" UID: {} ", uid)
        } else {
            " UID: N/A ".to_string()
        }
    }

    fn calc_spans_width(&self, spans: &[Span]) -> u16 {
        spans.iter().map(|s| s.content.width()).sum::<usize>() as u16
    }

    fn render_spans(&self, spans: &[Span], area: Rect, buf: &mut Buffer) {
        let line = Line::from(spans.to_vec());
        let paragraph = Paragraph::new(line);
        paragraph.render(area, buf);
    }

    fn render_focus_shortcuts(&self, app_model: &AppModel, area: Rect, buf: &mut Buffer) {
        let shortcuts = shortcuts_for_focus(app_model);
        if shortcuts.is_empty() {
            return;
        }

        // 构建快捷键文本：格式为 " | key:desc key:desc ..."
        let mut text = String::from(" | ");
        for (idx, shortcut) in shortcuts.iter().enumerate() {
            if idx > 0 {
                text.push(' ');
            }
            text.push_str(shortcut.key);
            text.push(':');
            text.push_str(shortcut.desc);
        }

        let available_width = area.width as usize;
        let text_width = text.width();

        // 根据可用宽度决定显示策略
        let display_text = if text_width <= available_width {
            // 完整显示
            text
        } else if available_width >= 3 {
            // 裁剪并显示 ...
            let mut truncated = String::from(" | ");
            let mut current_width = truncated.width();

            for shortcut in &shortcuts {
                let part = format!("{} {} ", shortcut.key, shortcut.desc);
                let part_width = part.width();

                if current_width + part_width + 3 <= available_width {
                    truncated.push_str(&part);
                    current_width += part_width;
                } else {
                    truncated.push_str("...");
                    break;
                }
            }

            truncated
        } else {
            // 空间太小，不显示
            String::new()
        };

        let span = Span::styled(display_text, Style::default().fg(Color::White));
        self.render_spans(&[span], area, buf);
    }
}

struct Shortcut<'a> {
    key: &'a str,
    desc: &'a str,
}

impl<'a> Shortcut<'a> {
    fn new(key: &'a str, desc: &'a str) -> Self {
        Self { key, desc }
    }
}

fn shortcuts_for_focus(app_model: &AppModel) -> Vec<Shortcut<'_>> {
    match app_model.focus_path.last() {
        Some(app::FocusNode::Home) => {
            let mut shortcuts = vec![
                Shortcut::new("a", i18n::loc(I18nKey::TuiFooterShortcutAccount)),
                Shortcut::new("u", i18n::loc(I18nKey::TuiFooterShortcutUpdate)),
                Shortcut::new("d", i18n::loc(I18nKey::TuiFooterShortcutImportExport)),
            ];
            match app_model.home_mode {
                app::HomeMode::Welcome => shortcuts,
                app::HomeMode::Data => {
                    shortcuts.extend(vec![
                        Shortcut::new("←→/Tab", i18n::loc(I18nKey::TuiFooterShortcutSwitchTab)),
                        Shortcut::new("↑↓", i18n::loc(I18nKey::TuiFooterShortcutScroll)),
                    ]);
                    shortcuts
                }
            }
        }
        Some(app::FocusNode::AccountList) => {
            vec![
                Shortcut::new("+", i18n::loc(I18nKey::TuiFooterShortcutAdd)),
                Shortcut::new("-", i18n::loc(I18nKey::TuiFooterShortcutDelete)),
                Shortcut::new("Enter", i18n::loc(I18nKey::TuiFooterShortcutLogin)),
                Shortcut::new("↑↓", i18n::loc(I18nKey::TuiFooterShortcutSelect)),
                Shortcut::new("Esc", i18n::loc(I18nKey::TuiFooterShortcutReturn)),
            ]
        }
        Some(app::FocusNode::AddAccount) => {
            vec![
                Shortcut::new("Enter", i18n::loc(I18nKey::TuiFooterShortcutAdd)),
                Shortcut::new("Esc", i18n::loc(I18nKey::TuiFooterShortcutReturn)),
            ]
        }
        Some(app::FocusNode::DeleteAccount) => {
            vec![
                Shortcut::new("Y", i18n::loc(I18nKey::TuiFooterShortcutDelete)),
                Shortcut::new("N/Esc", i18n::loc(I18nKey::TuiCancel)),
            ]
        }
        Some(app::FocusNode::UpdateMenu | app::FocusNode::ImportExportMenu) => {
            vec![
                Shortcut::new("↑↓", i18n::loc(I18nKey::TuiFooterShortcutSelect)),
                Shortcut::new("Esc", i18n::loc(I18nKey::TuiFooterShortcutReturn)),
            ]
        }
        Some(app::FocusNode::ImportFileList) => {
            vec![
                Shortcut::new("↑↓", i18n::loc(I18nKey::TuiFooterShortcutSelect)),
                Shortcut::new("f", i18n::loc(I18nKey::TuiFooterShortcutRefresh)),
                Shortcut::new("Enter", i18n::loc(I18nKey::TuiFooterShortcutImport)),
                Shortcut::new("Esc", i18n::loc(I18nKey::TuiFooterShortcutReturn)),
            ]
        }
        Some(app::FocusNode::Setting) => {
            vec![
                Shortcut::new("Tab/↑↓", i18n::loc(I18nKey::TuiFooterShortcutSelect)),
                Shortcut::new("←→", i18n::loc(I18nKey::TuiFooterShortcutSwitchValue)),
                Shortcut::new("Ctrl+S", i18n::loc(I18nKey::TuiFooterShortcutSave)),
            ]
        }
        Some(app::FocusNode::SettingSaveConfirm) => {
            vec![
                Shortcut::new("Enter", i18n::loc(I18nKey::TuiConfirm)),
                Shortcut::new("Esc", i18n::loc(I18nKey::TuiCancel)),
            ]
        }
        Some(app::FocusNode::Help) => {
            vec![
                Shortcut::new("a", i18n::loc(I18nKey::TuiFooterShortcutAbout)),
                Shortcut::new("↑↓", i18n::loc(I18nKey::TuiFooterShortcutScroll)),
            ]
        }
        None => vec![],
    }
}
