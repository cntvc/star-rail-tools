use crossterm::event::{KeyCode, KeyEvent};
use ratatui::Frame;
use ratatui::layout::{Alignment, Constraint, Layout, Rect};
use ratatui::style::{Color, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, BorderType, Borders, Clear, Paragraph, Widget};

use crate::action::{Action, RouteRequest};
use crate::app::{AppModel, FocusNode};

pub struct HelpWidget;

impl HelpWidget {
    pub fn new() -> Self {
        Self
    }

    pub fn render(&self, app_model: &mut AppModel, area: Rect, frame: &mut Frame) {
        self.render_help_content(area, frame);
        match app_model.focus_path.as_slice() {
            [FocusNode::Help, FocusNode::About] => AboutWidget::render(area, frame),
            _ => {}
        }
    }

    fn render_help_content(&self, area: Rect, frame: &mut Frame) {
        let help_lines = vec![
            Line::from(""),
            Line::from("═══ 软件简介 ═══"),
            Line::from(""),
            Line::from("星穹铁道抽卡记录工具"),
            Line::from("版本: v3.0.0"),
            Line::from(""),
            Line::from("一个本地化的抽卡记录管理和分析工具"),
            Line::from("所有数据存储在本地，绝不上传用户数据"),
            Line::from(""),
            Line::from("═══ 快捷键列表 ═══"),
            Line::from(""),
            Line::from("全局快捷键:"),
            Line::from("  a       - 账户管理"),
            Line::from("  u       - 更新记录"),
            Line::from("  ?       - 帮助"),
            Line::from("  ctrl+q  - 退出程序"),
            Line::from(""),
            Line::from("数据展示页:"),
            Line::from("  ←→      - 切换卡池"),
            Line::from("  ↑↓      - 滚动列表"),
            Line::from("  1-4     - 快速切换卡池"),
            Line::from(""),
            Line::from("对话框/弹窗:"),
            Line::from("  ↑↓      - 选择"),
            Line::from("  Enter   - 确认"),
            Line::from("  Esc     - 返回/取消"),
        ];

        let paragraph = Paragraph::new(help_lines)
            .style(Style::default())
            .alignment(Alignment::Left);

        frame.render_widget(paragraph, area);
    }

    pub fn handle_key_event(&self, key: KeyEvent, focus_path: &[FocusNode]) -> Option<Action> {
        match focus_path {
            [FocusNode::Help] => match key.code {
                KeyCode::Char('a') | KeyCode::Char('A') => {
                    Some(Action::Route(RouteRequest::OpenAbout))
                }
                _ => None,
            },
            [FocusNode::Help, FocusNode::About] => match key.code {
                KeyCode::Esc => Some(Action::Route(RouteRequest::Close)),
                _ => None,
            },
            _ => None,
        }
    }
}

pub struct AboutWidget;

impl AboutWidget {
    pub fn render(area: Rect, frame: &mut Frame) {
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
            .title("关于")
            .title_alignment(Alignment::Left);

        let inner_area = block.inner(center_area);
        block.render(center_area, frame.buffer_mut());

        let layout = Layout::vertical([
            Constraint::Length(1), // 空行
            Constraint::Length(1), // 项目名称
            Constraint::Length(1), // 空行
            Constraint::Length(1), // 版本
            Constraint::Length(1), // 空行
            Constraint::Length(1), // 开源协议
            Constraint::Length(1), // 仓库
            Constraint::Length(1), // 空行
        ]);

        let [
            _,
            title_area,
            _,
            version_area,
            _,
            license_area,
            repo_area,
            _,
        ] = layout.areas(inner_area);

        let title = Paragraph::new("星穹铁道抽卡记录工具")
            .style(Style::default())
            .alignment(Alignment::Center);
        frame.render_widget(title, title_area);

        let version = Paragraph::new(Line::from(vec![
            Span::styled("版本: ", Style::default()),
            Span::styled("v3.0.0", Style::default().fg(Color::Green)),
        ]))
        .alignment(Alignment::Center);
        frame.render_widget(version, version_area);

        let license = Paragraph::new("开源协议: GPL-3.0")
            .style(Style::default())
            .alignment(Alignment::Center);
        frame.render_widget(license, license_area);

        let repo = Paragraph::new("仓库: github.com/cntvc/star-rail-tools")
            .style(Style::default())
            .alignment(Alignment::Center);
        frame.render_widget(repo, repo_area);
    }
}
