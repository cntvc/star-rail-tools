use crossterm::event::{KeyCode, KeyEvent};
use ratatui::{
    Frame,
    layout::{Alignment, Constraint, Rect},
    style::{Color, Style},
    widgets::{
        Block, BorderType, Borders, Clear, List, ListItem, ListState, StatefulWidget, Widget,
    },
};
use unicode_width::UnicodeWidthStr;

use crate::action::{Action, GachaAction, RouteRequest};
use i18n::I18nKey;

pub struct RefreshMenuWidget {
    selected_index: ListState,
}

impl RefreshMenuWidget {
    pub fn new() -> Self {
        let mut selected_index = ListState::default();
        selected_index.select(Some(0));
        Self { selected_index }
    }

    pub fn render(&mut self, area: Rect, frame: &mut Frame) {
        // 选择最长的字符串长度
        let popup_width = i18n::loc(I18nKey::TuiRefreshIncremental).width() as u16 + 6;
        let popup_height = 4;

        let center_area = area.centered(
            Constraint::Length(popup_width),
            Constraint::Length(popup_height),
        );

        Clear.render(center_area, frame.buffer_mut());

        let block = Block::default()
            .borders(Borders::ALL)
            .border_type(BorderType::Rounded)
            .title(i18n::loc(I18nKey::TuiRefreshMenuTitle))
            .title_alignment(Alignment::Left);

        let items = vec![
            ListItem::new(i18n::loc(I18nKey::TuiRefreshIncremental)),
            ListItem::new(i18n::loc(I18nKey::TuiRefreshFull)),
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
                if let Some(selected) = self.selected_index.selected() {
                    if selected == 0 {
                        return Some(Action::Gacha(GachaAction::Refresh(false)));
                    } else {
                        return Some(Action::Gacha(GachaAction::Refresh(true)));
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
