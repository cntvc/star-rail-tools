use crossterm::event::{KeyCode, KeyEvent};
use ratatui::{
    Frame,
    layout::{Alignment, Constraint, Rect},
    style::{Color, Style},
    text::{Line, Span},
    widgets::{
        Block, BorderType, Borders, Clear, List, ListItem, ListState, Paragraph, StatefulWidget,
        Widget,
    },
};
use unicode_width::UnicodeWidthStr;

use crate::action::{Action, ExportAction, RouteRequest};
use crate::app::{AppModel, FocusNode};
use i18n::I18nKey;

pub struct ImportExportWidget {
    import_export_menu_widget: ImportExportMenuWidget,
}

impl ImportExportWidget {
    pub fn new() -> Self {
        Self {
            import_export_menu_widget: ImportExportMenuWidget::new(),
        }
    }

    pub fn handle_key_event(&mut self, key: KeyEvent, focus_node: &[FocusNode]) -> Option<Action> {
        match focus_node {
            [FocusNode::ImportExportMenu] => self.import_export_menu_widget.handle_key_event(key),
            [FocusNode::ImportExportMenu, FocusNode::ImportFileList] => {
                ImportListWidget::handle_key_event(key)
            }
            _ => None,
        }
    }

    pub fn render(&mut self, app_model: &mut AppModel, area: Rect, frame: &mut Frame) {
        match app_model.focus_path.last() {
            Some(FocusNode::ImportExportMenu) => self.import_export_menu_widget.render(area, frame),
            Some(FocusNode::ImportFileList) => ImportListWidget::render(app_model, area, frame),
            _ => {}
        }
    }
}

struct ImportExportMenuWidget {
    selected_index: ListState,
}

impl ImportExportMenuWidget {
    pub fn new() -> Self {
        let mut selected_index = ListState::default();
        selected_index.select(Some(0));
        Self { selected_index }
    }

    pub fn render(&mut self, area: Rect, frame: &mut Frame) {
        let popup_width = i18n::loc(I18nKey::TuiImportExportMenuTitle).width() as u16 + 6;
        let popup_height = 4;

        let center_area = area.centered(
            Constraint::Length(popup_width),
            Constraint::Length(popup_height),
        );

        Clear.render(center_area, frame.buffer_mut());

        let block = Block::default()
            .borders(Borders::ALL)
            .border_type(BorderType::Rounded)
            .title(i18n::loc(I18nKey::TuiImportExportMenuTitle))
            .title_alignment(Alignment::Left);

        let items = vec![
            ListItem::new(i18n::loc(I18nKey::TuiImportData)),
            ListItem::new(i18n::loc(I18nKey::TuiExportData)),
        ];

        let list = List::new(items)
            .block(block)
            .highlight_style(Style::default().fg(Color::Yellow))
            .highlight_symbol("> ");

        StatefulWidget::render(
            list,
            center_area,
            frame.buffer_mut(),
            &mut self.selected_index,
        );
    }

    pub fn handle_key_event(&mut self, key: KeyEvent) -> Option<Action> {
        match key.code {
            KeyCode::Down => {
                self.select_next();
                None
            }
            KeyCode::Up => {
                self.select_prev();
                None
            }
            KeyCode::Enter => {
                if let Some(i) = self.selected_index.selected() {
                    if i == 0 {
                        return Some(Action::Route(RouteRequest::OpenImportFileList));
                    } else {
                        return Some(Action::Export(ExportAction::Export));
                    }
                }
                None
            }
            KeyCode::Esc => {
                self.selected_index.select(Some(0));
                Some(Action::Route(RouteRequest::Close))
            }
            _ => None,
        }
    }

    fn select_prev(&mut self) {
        let current = self.selected_index.selected().unwrap_or(0);
        let prev = (current + 1) % 2;
        self.selected_index.select(Some(prev));
    }

    fn select_next(&mut self) {
        let current = self.selected_index.selected().unwrap_or(0);
        let next = (current + 1) % 2;
        self.selected_index.select(Some(next));
    }
}

struct ImportListWidget;

impl ImportListWidget {
    pub fn render(app_model: &mut AppModel, area: Rect, frame: &mut Frame) {
        let popup_width = 40;
        let popup_height = 10;

        let center_area = area.centered(
            Constraint::Length(popup_width),
            Constraint::Length(popup_height),
        );

        Clear.render(center_area, frame.buffer_mut());

        let block = Block::default()
            .borders(Borders::ALL)
            .border_type(BorderType::Rounded)
            .title(i18n::loc(I18nKey::TuiSelectImportFile))
            .title_alignment(Alignment::Left);

        let inner_area = block.inner(center_area);
        block.render(center_area, frame.buffer_mut());

        if app_model.import_file_list.is_empty() {
            Self::render_empty_hint(inner_area, frame);
        } else {
            Self::render_file_list(app_model, inner_area, frame);
        }
    }

    fn render_empty_hint(area: Rect, frame: &mut Frame) {
        let text = vec![
            Line::from(""),
            Line::from(Span::styled(
                i18n::loc(I18nKey::TuiImportNoFilesFound),
                Style::default().fg(Color::Yellow),
            )),
            Line::from(""),
            Line::from(Span::styled(
                i18n::loc(I18nKey::TuiImportFilesHint),
                Style::default().fg(Color::Gray),
            )),
        ];

        let paragraph = Paragraph::new(text)
            .alignment(Alignment::Center)
            .wrap(ratatui::widgets::Wrap { trim: true });
        frame.render_widget(paragraph, area);
    }

    fn render_file_list(app_model: &mut AppModel, inner_area: Rect, frame: &mut Frame) {
        let items: Vec<ListItem> = app_model
            .import_file_list
            .iter()
            .filter_map(|path| {
                path.file_name()
                    .and_then(|name| name.to_str())
                    .map(|name| ListItem::new(name))
            })
            .collect();

        let list = List::new(items)
            .highlight_style(Style::default().fg(Color::Yellow))
            .highlight_symbol("> ");

        StatefulWidget::render(
            list,
            inner_area,
            frame.buffer_mut(),
            &mut app_model.import_file_list_index,
        );
    }

    pub fn handle_key_event(key: KeyEvent) -> Option<Action> {
        use crate::action::ImportAction;

        match key.code {
            KeyCode::Down => Some(Action::Import(ImportAction::SelectNext)),
            KeyCode::Up => Some(Action::Import(ImportAction::SelectPrev)),
            KeyCode::Enter => Some(Action::Import(ImportAction::Import)),
            KeyCode::Char('f') | KeyCode::Char('F') => Some(Action::Import(ImportAction::ScanFile)),
            KeyCode::Esc => Some(Action::Route(RouteRequest::Close)),
            _ => None,
        }
    }
}
