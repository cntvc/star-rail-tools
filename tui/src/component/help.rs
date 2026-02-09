use crossterm::event::{KeyCode, KeyEvent};
use ratatui::{
    Frame,
    layout::{Constraint, Rect},
    style::{Color, Style},
    text::{Line, Span},
    widgets::{Paragraph, Widget, Wrap},
};

use crate::action::{Action, RouteRequest};
use crate::app::{AppModel, FocusNode};
use i18n::I18nKey;

pub struct HelpWidget {
    scroll_offset: u16,
    total_lines: u16,
    view_height: u16,
}

impl HelpWidget {
    pub fn new() -> Self {
        Self {
            scroll_offset: 0,
            total_lines: 0,
            view_height: 0,
        }
    }

    pub fn render(&mut self, _app_model: &mut AppModel, area: Rect, frame: &mut Frame) {
        self.view_height = area.height;

        let content_width = (area.width * 60 / 100).max(70).min(area.width);

        let content = generate_content(content_width as usize);

        self.total_lines = calculate_total_lines(&content, content_width);

        let center_area = area.centered(Constraint::Length(content_width), Constraint::Fill(1));

        Paragraph::new(content)
            .style(Style::default())
            .wrap(Wrap { trim: true })
            .scroll((self.scroll_offset, 0))
            .render(center_area, frame.buffer_mut());
    }

    pub fn handle_key_event(&mut self, key: KeyEvent, focus_path: &[FocusNode]) -> Option<Action> {
        match focus_path {
            [FocusNode::Help] => match key.code {
                KeyCode::Down => {
                    self.scroll_down();
                    None
                }
                KeyCode::Up => {
                    self.scroll_up();
                    None
                }
                KeyCode::PageDown => {
                    self.scroll_offset = self.scroll_offset.saturating_add(10);
                    None
                }
                KeyCode::PageUp => {
                    self.scroll_offset = self.scroll_offset.saturating_sub(10);
                    None
                }
                KeyCode::Esc => Some(Action::Route(RouteRequest::Close)),
                _ => None,
            },
            _ => None,
        }
    }

    fn scroll_down(&mut self) {
        let max_scroll = self.total_lines.saturating_sub(self.view_height);
        if self.scroll_offset < max_scroll {
            self.scroll_offset = (self.scroll_offset + 5).min(max_scroll);
        }
    }

    fn scroll_up(&mut self) {
        self.scroll_offset = self.scroll_offset.saturating_sub(5);
    }
}

fn calculate_total_lines(content: &[Line], max_width: u16) -> u16 {
    let max_width = max_width as usize;
    if max_width == 0 {
        return 0;
    }

    let mut count = 0;
    for line in content {
        let line_width = line.width();
        if line_width == 0 {
            count += 1; // 空行也占一行
        } else {
            // 简单的向上取整计算
            // 注意：这只是估算，Ratatui 的 wrap 逻辑可能更复杂（处理单词边界），
            // 但对于中英文混排且以中文为主的内容，按字符宽度估算通常足够接近。
            // 如果是纯英文长单词，Ratatui 可能会提前换行导致我们少算行数，
            // 但考虑到 context 是帮助文档，这种情况较少。
            count += line_width.div_ceil(max_width);
        }
    }
    count as u16
}

fn text_to_lines(text: &str) -> Vec<Line<'static>> {
    text.lines().map(|s| Line::from(s.to_string())).collect()
}

fn generate_content(width: usize) -> Vec<Line<'static>> {
    let separator_str = "═".repeat(width);
    let separator = Line::from(separator_str).style(Style::default().fg(Color::DarkGray));

    let empty_line = Line::from("");

    let mut lines = Vec::new();

    lines.push(empty_line.clone());
    lines.push(
        Line::from(format!("{} v{}", srt::APP_NAME, srt::APP_VERSION))
            .style(Style::default().fg(Color::Cyan).bold())
            .centered(),
    );
    lines.push(empty_line.clone());

    // Intro
    lines.push(separator.clone());
    lines.push(Line::from(i18n::loc(I18nKey::TuiHelpIntroTitle)).centered());
    lines.push(separator.clone());
    lines.push(empty_line.clone());
    lines.extend(text_to_lines(i18n::loc(I18nKey::TuiHelpIntroDesc)));
    lines.push(empty_line.clone());

    // Import/Export
    lines.push(separator.clone());
    lines.push(Line::from(i18n::loc(I18nKey::TuiHelpImportExportTitle)).centered());
    lines.push(separator.clone());
    lines.push(empty_line.clone());
    lines.extend(text_to_lines(i18n::loc(I18nKey::TuiHelpImportGuide)));
    lines.push(empty_line.clone());

    // UIGF
    lines.push(separator.clone());
    lines.push(Line::from(i18n::loc(I18nKey::TuiHelpUigfTitle)).centered());
    lines.push(separator.clone());
    lines.push(empty_line.clone());
    lines.extend(text_to_lines(i18n::loc(I18nKey::TuiHelpUigfDesc)));
    lines.push(empty_line.clone());
    // Website link
    lines.push(Line::from(Span::styled(
        i18n::loc(I18nKey::TuiHelpUigfWebsite),
        Style::default().fg(Color::Cyan),
    )));
    lines.push(empty_line.clone());

    // Errors
    lines.push(separator.clone());
    lines.push(Line::from(i18n::loc(I18nKey::TuiHelpErrorsTitle)).centered());
    lines.push(separator.clone());
    lines.push(empty_line.clone());
    lines.extend(text_to_lines(i18n::loc(I18nKey::TuiHelpErrorMetadata)));
    lines.push(empty_line.clone());

    // Privacy
    lines.push(separator.clone());
    lines.push(Line::from(i18n::loc(I18nKey::TuiHelpPrivacyTitle)).centered());
    lines.push(separator.clone());
    lines.push(empty_line.clone());
    lines.extend(text_to_lines(i18n::loc(I18nKey::TuiHelpPrivacyDesc)));
    lines.push(empty_line.clone());

    lines
}
