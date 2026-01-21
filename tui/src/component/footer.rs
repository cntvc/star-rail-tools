use ratatui::layout::{Constraint, Layout};
use unicode_width::UnicodeWidthStr;

use ratatui::{
    buffer::Buffer,
    layout::Rect,
    style::{Color, Style},
    text::{Line, Span},
    widgets::{Paragraph, Widget},
};

use crate::app::{self, AppModel, FocusNode};

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

        // 渲染全局菜单
        self.render_spans(&global_menu_spans, global_area, buf);

        // 渲染 UID
        let uid_span = Span::styled(uid_text, Style::default().fg(Color::White));
        self.render_spans(&[uid_span], uid_area, buf);

        // 第二层布局：焦点快捷键 | 任务进度
        // 目前任务进度为空，所以全部空间给焦点快捷键
        let task_progress_width = 0u16; // TODO: 实现任务进度时修改

        let [shortcuts_area, _task_area] =
            Layout::horizontal([Constraint::Min(1), Constraint::Length(task_progress_width)])
                .areas(middle_area);

        // 渲染焦点快捷键
        self.render_focus_shortcuts(app_model, shortcuts_area, buf);
    }

    fn build_global_menu_spans(&self, app_model: &AppModel) -> Vec<Span<'static>> {
        let current_root = app_model.focus_path.root_path();

        let style = Style::default().fg(Color::White);
        let highlight_style = Style::default().fg(Color::Yellow).bold();
        let mut spans = Vec::new();

        let home_style = if current_root == Some(FocusNode::Home) {
            highlight_style
        } else {
            style
        };
        spans.push(Span::styled("[主页(h)]".to_string(), home_style));

        spans.push(Span::raw(" "));
        spans.push(Span::styled("[设置(s)]".to_string(), style));

        spans.push(Span::raw(" "));
        spans.push(Span::styled("[帮助(?)]".to_string(), style));

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
            vec![
                Shortcut::new("a", "账户"),
                Shortcut::new("u", "更新"),
                Shortcut::new("◄ ►", "切换"),
            ]
        }
        Some(app::FocusNode::AccountList) => {
            vec![
                Shortcut::new("+", "添加"),
                Shortcut::new("-", "删除"),
                Shortcut::new("Enter", "登录"),
                Shortcut::new("▲ ▼", "选择"),
                Shortcut::new("Esc", "返回"),
            ]
        }
        Some(app::FocusNode::AddAccount) => {
            vec![Shortcut::new("Enter", "添加"), Shortcut::new("Esc", "返回")]
        }
        Some(app::FocusNode::DeleteAccount) => {
            vec![Shortcut::new("Y", "删除"), Shortcut::new("N/Esc", "取消")]
        }
        Some(app::FocusNode::UpdateMenu) => {
            vec![Shortcut::new("▲ ▼", "选择"), Shortcut::new("Esc", "返回")]
        }
        None => vec![],
    }
}
