use crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::{
    Frame,
    layout::{Alignment, Constraint, Layout, Rect},
    style::{Color, Style},
    text::{Line, Span},
    widgets::{Block, BorderType, Borders, Clear, Paragraph, Widget},
};

use crate::{
    action::{Action, RouteRequest, SettingAction},
    app::{AppModel, FocusNode},
};
use i18n::I18nKey;
use srt::ConfigItem;

pub const SETTING_ITEMS: [ConfigItem; 3] = ConfigItem::as_array();

pub struct SettingWidget;

impl SettingWidget {
    pub fn handle_key_event(key: KeyEvent, focus_path: &[FocusNode]) -> Option<Action> {
        match focus_path {
            [FocusNode::Setting] => match key.code {
                KeyCode::Up | KeyCode::BackTab => Some(Action::Setting(SettingAction::Select(-1))),
                KeyCode::Down | KeyCode::Tab => Some(Action::Setting(SettingAction::Select(1))),
                KeyCode::Left => Some(Action::Setting(SettingAction::Increment(-1))),
                KeyCode::Right => Some(Action::Setting(SettingAction::Increment(1))),
                KeyCode::Char('h') | KeyCode::Char('H') => {
                    Some(Action::Route(RouteRequest::SwitchToHome))
                }
                KeyCode::Char('?') | KeyCode::Char('/') => {
                    Some(Action::Route(RouteRequest::SwitchToHelp))
                }
                KeyCode::Char('s') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                    Some(Action::Route(RouteRequest::OpenSaveSettingConfirm))
                }
                _ => None,
            },
            [FocusNode::Setting, FocusNode::SettingSaveConfirm] => {
                SettingSaveConfirmWidget::handle_key_event(key)
            }
            _ => None,
        }
    }

    pub fn render(app_model: &AppModel, area: Rect, frame: &mut Frame) {
        let content_width = 50;
        let content_height = 12;

        let center_area = area.centered(
            Constraint::Length(content_width),
            Constraint::Length(content_height),
        );

        let [title_area, items_area] =
            Layout::vertical([Constraint::Length(3), Constraint::Min(0)]).areas(center_area);

        let separator = Line::from("═".repeat(content_width as usize))
            .style(Style::default().fg(Color::DarkGray));

        Paragraph::new(vec![
            separator.clone(),
            Line::from(i18n::loc(I18nKey::TuiSettingTitle)),
            separator,
        ])
        .alignment(Alignment::Center)
        .render(title_area, frame.buffer_mut());

        Self::render_settings(app_model, items_area, frame);

        if let [FocusNode::Setting, FocusNode::SettingSaveConfirm] = app_model.focus_path.as_slice()
        {
            SettingSaveConfirmWidget::render(area, frame);
        }
    }

    fn get_item_label(item: ConfigItem) -> &'static str {
        match item {
            ConfigItem::Language => i18n::loc(I18nKey::TuiSettingLanguage),
            ConfigItem::CheckUpdate => i18n::loc(I18nKey::TuiSettingAutoCheckUpdate),
            ConfigItem::LogLevel => i18n::loc(I18nKey::TuiSettingLogLevel),
        }
    }

    fn get_item_value_display(item: ConfigItem, config: &srt::AppConfig) -> String {
        match item {
            ConfigItem::Language => format!("[{}]", get_language_display(config.language)),
            ConfigItem::CheckUpdate => {
                format!("[{}]", if config.check_update { "ON" } else { "OFF" })
            }
            ConfigItem::LogLevel => format!("[{}]", config.log_level),
        }
    }

    fn render_settings(app_model: &AppModel, area: Rect, frame: &mut Frame) {
        let constraints = (0..SETTING_ITEMS.len()).map(|_| Constraint::Length(3));
        let items_area = Layout::vertical(constraints).split(area);

        for (i, item) in SETTING_ITEMS.iter().enumerate() {
            Self::render_setting_item(
                app_model.config_item_index == i,
                Self::get_item_label(*item),
                &Self::get_item_value_display(*item, &app_model.temporary_config),
                items_area[i],
                frame,
            );
        }
    }

    fn render_setting_item(
        is_highlight: bool,
        label: &str,
        value: &str,
        area: Rect,
        frame: &mut Frame,
    ) {
        let rows = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Min(0),
        ])
        .split(area);

        let content_area = rows[1];

        let [label_area, value_area] =
            Layout::horizontal([Constraint::Fill(1), Constraint::Fill(1)]).areas(content_area);

        let style = if is_highlight {
            Style::default().fg(Color::Cyan)
        } else {
            Style::default().fg(Color::White)
        };

        let label_widget = Paragraph::new(label)
            .style(style)
            .alignment(Alignment::Left);
        frame.render_widget(label_widget, label_area);

        let value_widget = Paragraph::new(value)
            .style(style)
            .alignment(Alignment::Right);
        frame.render_widget(value_widget, value_area);
    }
}

fn get_language_display(lang: i18n::Lang) -> &'static str {
    match lang {
        i18n::Lang::zh_cn => "中文",
        i18n::Lang::en_us => "English",
    }
}

struct SettingSaveConfirmWidget;

impl SettingSaveConfirmWidget {
    pub fn render(area: Rect, frame: &mut Frame) {
        let popup_width = 40;
        let popup_height = 9;

        let center_area = area.centered(
            Constraint::Length(popup_width),
            Constraint::Length(popup_height),
        );

        Clear.render(center_area, frame.buffer_mut());

        let block = Block::default()
            .borders(Borders::ALL)
            .border_type(BorderType::Rounded)
            .title_alignment(Alignment::Left)
            .border_style(Style::default().fg(Color::White));

        let inner_area = block.inner(center_area);
        frame.render_widget(block, center_area);

        let message = vec![
            Line::from(""),
            Line::from(Span::styled(
                i18n::loc(I18nKey::TuiSettingSaveConfirm),
                Style::default().fg(Color::White),
            )),
            Line::from(""),
            Line::from(vec![
                Span::styled("[Enter] ", Style::default().fg(Color::White)),
                Span::raw(i18n::loc(I18nKey::TuiConfirm)),
                Span::raw("  "),
                Span::styled("[Esc] ", Style::default().fg(Color::White)),
                Span::raw(i18n::loc(I18nKey::TuiCancel)),
            ]),
        ];

        let paragraph = Paragraph::new(message).alignment(Alignment::Center);
        frame.render_widget(paragraph, inner_area);
    }

    pub fn handle_key_event(key: KeyEvent) -> Option<Action> {
        match key.code {
            KeyCode::Enter => Some(Action::Setting(SettingAction::Save)),
            KeyCode::Esc => Some(Action::Route(RouteRequest::Close)),
            _ => None,
        }
    }
}
