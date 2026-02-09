use crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::{
    Frame,
    layout::{Alignment, Constraint, Layout, Rect},
    style::{Color, Style},
    text::{Line, Span},
    widgets::{Block, BorderType, Borders, Clear, Paragraph, Widget},
};

use srt::{AppConfig, logger::Level};

use crate::{
    action::{Action, RouteRequest, SettingAction},
    app::{AppModel, FocusNode},
};
use i18n::I18nKey;

pub struct SettingWidget {
    selected_index: usize,
    temp_config: AppConfig,
    save_confirm_widget: SettingSaveConfirmWidget,
}

impl SettingWidget {
    const SETTING_COUNT: usize = 3;

    pub fn new() -> Self {
        Self {
            selected_index: 0,
            temp_config: AppConfig::default(),
            save_confirm_widget: SettingSaveConfirmWidget::new(),
        }
    }

    pub fn handle_key_event(&mut self, key: KeyEvent, focus_path: &[FocusNode]) -> Option<Action> {
        match focus_path {
            [FocusNode::Setting] => match key.code {
                KeyCode::Up | KeyCode::BackTab => {
                    self.select_prev();
                    None
                }
                KeyCode::Down | KeyCode::Tab => {
                    self.select_next();
                    None
                }
                KeyCode::Left => {
                    self.decrease_value();
                    None
                }
                KeyCode::Right => {
                    self.increase_value();
                    None
                }
                KeyCode::Char('s') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                    self.save_confirm_widget.set_config(self.temp_config);
                    Some(Action::Route(RouteRequest::OpenSaveSettingConfirm))
                }
                KeyCode::Esc => Some(Action::Route(RouteRequest::Close)),
                _ => None,
            },
            [FocusNode::Setting, FocusNode::SettingSaveConfirm] => {
                self.save_confirm_widget.handle_key_event(key)
            }
            _ => None,
        }
    }

    pub fn load_config(&mut self, config: &AppConfig) {
        self.temp_config = *config;
    }

    pub fn render(&self, app_model: &AppModel, area: Rect, frame: &mut Frame) {
        let content_width = 50;
        let content_height = 12;

        let center_area = area.centered(
            Constraint::Length(content_width),
            Constraint::Length(content_height),
        );

        let [title_area, items_area] =
            Layout::vertical([Constraint::Length(3), Constraint::Min(0)]).areas(center_area);

        Paragraph::new(i18n::loc(I18nKey::TuiSettingTitle))
            .alignment(Alignment::Center)
            .block(
                Block::default()
                    .borders(Borders::BOTTOM)
                    .border_style(Style::default().fg(Color::DarkGray)),
            )
            .render(title_area, frame.buffer_mut());

        self.render_settings(items_area, frame);

        if let [FocusNode::Setting, FocusNode::SettingSaveConfirm] = app_model.focus_path.as_slice()
        {
            self.save_confirm_widget.render(area, frame);
        }
    }

    fn render_settings(&self, area: Rect, frame: &mut Frame) {
        let items_area = Layout::vertical([
            Constraint::Length(2),
            Constraint::Length(1),
            Constraint::Length(2),
            Constraint::Length(1),
            Constraint::Length(2),
            Constraint::Length(1),
        ])
        .split(area);

        self.render_setting_item(
            self.selected_index == 0,
            i18n::loc(I18nKey::TuiSettingLanguage),
            &format!("[{}]", self.get_language_display()),
            items_area[1],
            frame,
        );

        self.render_setting_item(
            self.selected_index == 1,
            i18n::loc(I18nKey::TuiSettingAutoCheckUpdate),
            &format!(
                "[{}]",
                if self.temp_config.check_update {
                    "ON"
                } else {
                    "OFF"
                }
            ),
            items_area[3],
            frame,
        );

        self.render_setting_item(
            self.selected_index == 2,
            i18n::loc(I18nKey::TuiSettingLogLevel),
            &format!("[{}]", self.temp_config.log_level),
            items_area[5],
            frame,
        );
    }

    fn render_setting_item(
        &self,
        is_highlight: bool,
        label: &str,
        value: &str,
        area: Rect,
        frame: &mut Frame,
    ) {
        let [label_area, value_area] =
            Layout::horizontal([Constraint::Fill(1), Constraint::Fill(1)]).areas(area);

        let label_style = if is_highlight {
            Style::default().fg(Color::Yellow)
        } else {
            Style::default().fg(Color::White)
        };

        let label_text = if is_highlight {
            format!("> {}", label)
        } else {
            format!("  {}", label)
        };

        let label_widget = Paragraph::new(label_text)
            .style(label_style)
            .alignment(Alignment::Left);
        frame.render_widget(label_widget, label_area);

        let value_style = if is_highlight {
            Style::default().fg(Color::Cyan)
        } else {
            Style::default().fg(Color::Gray)
        };

        let value_widget = Paragraph::new(value)
            .style(value_style)
            .alignment(Alignment::Right);
        frame.render_widget(value_widget, value_area);
    }

    fn select_prev(&mut self) {
        self.selected_index = (self.selected_index + Self::SETTING_COUNT - 1) % Self::SETTING_COUNT;
    }

    fn select_next(&mut self) {
        self.selected_index = (self.selected_index + 1) % Self::SETTING_COUNT;
    }

    fn increase_value(&mut self) {
        match self.selected_index {
            0 => {
                self.temp_config.language = match self.temp_config.language {
                    i18n::Lang::zh_cn => i18n::Lang::en_us,
                    i18n::Lang::en_us => i18n::Lang::zh_cn,
                };
            }
            1 => {
                self.temp_config.check_update = !self.temp_config.check_update;
            }
            2 => {
                self.temp_config.log_level = match self.temp_config.log_level {
                    Level::DEBUG => Level::INFO,
                    Level::INFO => Level::WARN,
                    Level::WARN => Level::ERROR,
                    Level::ERROR => Level::DEBUG,
                    _ => Level::DEBUG,
                };
            }
            _ => {}
        }
    }

    fn decrease_value(&mut self) {
        match self.selected_index {
            0 => {
                self.temp_config.language = match self.temp_config.language {
                    i18n::Lang::zh_cn => i18n::Lang::en_us,
                    i18n::Lang::en_us => i18n::Lang::zh_cn,
                };
            }
            1 => {
                self.temp_config.check_update = !self.temp_config.check_update;
            }
            2 => {
                self.temp_config.log_level = match self.temp_config.log_level {
                    Level::DEBUG => Level::ERROR,
                    Level::INFO => Level::DEBUG,
                    Level::WARN => Level::INFO,
                    Level::ERROR => Level::WARN,
                    _ => Level::ERROR,
                };
            }
            _ => {}
        }
    }

    fn get_language_display(&self) -> &str {
        match self.temp_config.language {
            i18n::Lang::zh_cn => "中文",
            i18n::Lang::en_us => "English",
        }
    }
}

struct SettingSaveConfirmWidget {
    config: AppConfig,
}

impl SettingSaveConfirmWidget {
    pub fn new() -> Self {
        Self {
            config: AppConfig::default(),
        }
    }

    pub fn set_config(&mut self, config: AppConfig) {
        self.config = config;
    }

    pub fn render(&self, area: Rect, frame: &mut Frame) {
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
            Line::from(Span::styled(
                i18n::loc(I18nKey::TuiSettingRestartHint),
                Style::default().fg(Color::Red),
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

    pub fn handle_key_event(&self, key: KeyEvent) -> Option<Action> {
        match key.code {
            KeyCode::Enter => Some(Action::Setting(SettingAction::Save(self.config))),
            KeyCode::Esc => Some(Action::Route(RouteRequest::Close)),
            _ => None,
        }
    }
}
