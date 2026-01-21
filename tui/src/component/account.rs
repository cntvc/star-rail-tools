use crossterm::event::{KeyCode, KeyEvent};
use ratatui::{
    DefaultTerminal, Frame,
    buffer::Buffer,
    layout::{Alignment, Constraint, Layout, Rect, Spacing},
    style::{Color, Modifier, Style, Stylize},
    symbols::{border, merge::MergeStrategy},
    text::{Line, Span},
    widgets::{
        Block, BorderType, Borders, Clear, List, ListItem, ListState, Paragraph, StatefulWidget,
        Widget,
    },
};
use srt::logger;
use tokio::sync::mpsc::{self, UnboundedReceiver, UnboundedSender};

use crate::action::{AccountAction, Action, RouteRequest};
use crate::app::{App, AppModel, FocusNode};

pub struct AccountListWidget {
    add_account_widget: AddAccountWidget,
    delete_account_widget: DeleteAccountWidget,
}

impl AccountListWidget {
    pub fn new() -> Self {
        Self {
            add_account_widget: AddAccountWidget::new(),
            delete_account_widget: DeleteAccountWidget::new(),
        }
    }

    pub fn render(&mut self, app_model: &mut AppModel, area: Rect, frame: &mut Frame) {
        match app_model.focus_path[1..] {
            [FocusNode::AccountList] => UidListWidget::render(app_model, area, frame),
            [FocusNode::AccountList, FocusNode::AddAccount, ..] => {
                self.add_account_widget.render(area, frame)
            }
            [FocusNode::AccountList, FocusNode::DeleteAccount, ..] => {
                self.delete_account_widget.render(app_model, area, frame)
            }
            _ => {}
        }
    }

    pub fn handle_key_event(&mut self, key: KeyEvent, focus_path: &[FocusNode]) -> Option<Action> {
        logger::info!("account menu handle_key_event: {:?}", focus_path);
        match focus_path {
            [FocusNode::AccountList] => UidListWidget::handle_key_event(key),
            [FocusNode::AccountList, FocusNode::AddAccount] => {
                self.add_account_widget.handle_key_event(key)
            }
            [FocusNode::AccountList, FocusNode::DeleteAccount] => {
                self.delete_account_widget.handle_key_event(key)
            }
            _ => None,
        }
    }
}

struct UidListWidget;

impl UidListWidget {
    fn render(app_model: &mut AppModel, area: Rect, frame: &mut Frame) {
        let content_height = app_model.uid_list.len() as u16;
        let total_height = (content_height + 2).min(10);

        let center_area = area.centered(Constraint::Length(19), Constraint::Length(total_height));

        let block = Block::default()
            .borders(Borders::ALL)
            .border_type(BorderType::Rounded)
            .title("账号列表")
            .title_alignment(Alignment::Left);

        let items: Vec<ListItem> = app_model
            .uid_list
            .iter()
            .enumerate()
            .map(|(idx, uid)| {
                let prefix = format!("[{}] ", idx + 1);
                ListItem::new(prefix + uid)
            })
            .collect();

        let list = List::new(items)
            .block(block)
            .highlight_style(Style::new().yellow())
            .highlight_symbol("> ");

        Clear.render(center_area, frame.buffer_mut());
        StatefulWidget::render(
            list,
            center_area,
            frame.buffer_mut(),
            &mut app_model.uid_list_index,
        );
    }

    pub fn handle_key_event(key: KeyEvent) -> Option<Action> {
        logger::info!("account list handle_key_event: {:?}", key.code);
        match key.code {
            KeyCode::Down => Some(Action::Account(AccountAction::SelectNext)),
            KeyCode::Up => Some(Action::Account(AccountAction::SelectPrev)),
            KeyCode::Char('+') | KeyCode::Char('=') => {
                Some(Action::Route(RouteRequest::OpenAddAccountWidget))
            }
            KeyCode::Char('-') | KeyCode::Char('_') => {
                Some(Action::Route(RouteRequest::OpenDeleteAccountWidget))
            }
            KeyCode::Enter => Some(Action::Account(AccountAction::StartLogin)),
            KeyCode::Esc => Some(Action::Route(RouteRequest::Close)),
            _ => None,
        }
    }
}

struct DeleteAccountWidget;

impl DeleteAccountWidget {
    fn new() -> Self {
        Self {}
    }

    fn render(&self, app_model: &AppModel, area: Rect, frame: &mut Frame) {
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
            .title("删除账户")
            .title_alignment(Alignment::Left);

        let inner_area = block.inner(center_area);
        block.render(center_area, frame.buffer_mut());

        // 获取当前选中的 UID
        let uid = app_model
            .uid_list
            .get(app_model.uid_list_index.selected().unwrap_or(0))
            .map(|s| s.as_str())
            .unwrap_or("未知");

        // 内部布局
        let layout = Layout::vertical([
            Constraint::Length(1), // 确认提示
            Constraint::Length(1), // UID 显示
            Constraint::Length(1), // 空行
            Constraint::Length(1), // 警告文字
            Constraint::Length(1), // 空行
            Constraint::Length(1), // Y 提示
            Constraint::Length(1), // N/Esc 提示
        ]);
        let [
            confirm_area,
            uid_area,
            _,
            warning_area,
            _,
            yes_area,
            no_area,
        ] = layout.areas(inner_area);

        let confirm_text = Paragraph::new("确定要删除该账户吗？")
            .style(Style::default())
            .alignment(Alignment::Center);
        frame.render_widget(confirm_text, confirm_area);

        let uid_text = Paragraph::new(format!("UID: {}", uid))
            .style(Style::default())
            .alignment(Alignment::Center);
        frame.render_widget(uid_text, uid_area);

        let warning_text = Paragraph::new("该账户下的所有抽卡记录将被永久删除")
            .style(Style::default().fg(Color::Red).bold())
            .alignment(Alignment::Center);
        frame.render_widget(warning_text, warning_area);

        let yes_text = Paragraph::new("按 Y 确认删除")
            .style(Style::default())
            .alignment(Alignment::Center);
        frame.render_widget(yes_text, yes_area);

        let no_text = Paragraph::new("按 N 或 Esc 取消")
            .style(Style::default())
            .alignment(Alignment::Center);
        frame.render_widget(no_text, no_area);
    }

    fn handle_key_event(&self, key: KeyEvent) -> Option<Action> {
        match key.code {
            KeyCode::Char('y') | KeyCode::Char('Y') => {
                Some(Action::Account(AccountAction::StartDelete))
            }
            KeyCode::Char('n') | KeyCode::Char('N') => Some(Action::Route(RouteRequest::Close)),
            KeyCode::Esc => Some(Action::Route(RouteRequest::Close)),
            _ => None,
        }
    }
}

pub struct AddAccountWidget {
    input_value: String,
}

impl AddAccountWidget {
    const MAX_LEN: usize = 9;
    pub fn new() -> Self {
        Self {
            input_value: String::new(),
        }
    }

    pub fn handle_key_event(&mut self, key: KeyEvent) -> Option<Action> {
        logger::info!("add account handle_key_event: {:?}", key.code);
        match key.code {
            KeyCode::Esc => {
                self.input_value.clear();
                Some(Action::Route(RouteRequest::Close))
            }
            KeyCode::Enter => {
                if self.input_value.len() == Self::MAX_LEN {
                    let uid = self.input_value.clone();
                    self.input_value.clear();
                    Some(Action::Account(AccountAction::StartAdd(uid)))
                } else {
                    None
                }
            }
            KeyCode::Char(c @ '0'..='9') => {
                if self.input_value.len() < Self::MAX_LEN {
                    self.input_value.push(c);
                }
                None
            }
            KeyCode::Backspace => {
                self.input_value.pop();
                None
            }
            _ => None,
        }
    }

    pub fn render(&self, area: Rect, frame: &mut Frame) {
        let popup_width = 23;
        let popup_height = 5;
        let center_area = area.centered(
            Constraint::Length(popup_width),
            Constraint::Length(popup_height),
        );

        Clear.render(center_area, frame.buffer_mut());

        let block = Block::default()
            .borders(Borders::ALL)
            .border_type(BorderType::Rounded)
            .title("添加账户")
            .title_alignment(Alignment::Left);

        let inner_area = block.inner(center_area);
        block.render(center_area, frame.buffer_mut());

        let [label_area, input_area, _] = Layout::vertical([
            Constraint::Length(1), // 标签
            Constraint::Length(1), // 输入框
            Constraint::Length(1), // 空行
        ])
        .areas(inner_area);

        let label = Paragraph::new("请输入 UID:")
            .style(Style::default())
            .alignment(Alignment::Center);
        frame.render_widget(label, label_area);

        let cursor_pos = self.input_value.len();

        let mut input_spans = vec![Span::raw("[")];

        for i in 0..Self::MAX_LEN {
            let ch = if i < self.input_value.len() {
                self.input_value.chars().nth(i).unwrap().to_string()
            } else {
                "_".to_string()
            };

            if i == cursor_pos {
                input_spans.push(Span::styled(
                    ch,
                    Style::default().fg(Color::Black).bg(Color::Yellow),
                ));
            } else {
                input_spans.push(Span::styled(ch, Style::default().fg(Color::Yellow)));
            }
        }

        input_spans.push(Span::raw("]"));

        let input_line = Paragraph::new(Line::from(input_spans)).alignment(Alignment::Center);
        frame.render_widget(input_line, input_area);
    }
}
