use std::collections::VecDeque;
use std::time::{Duration, Instant};

use ratatui::{
    buffer::Buffer,
    layout::{Constraint, Layout, Rect},
    style::{Color, Style},
    widgets::{Block, Borders, Clear, Paragraph, Widget, Wrap},
};
use serde::{Deserialize, Serialize};
use unicode_width::UnicodeWidthStr;

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub enum NotificationType {
    Info,
    Warning,
    Error,
}

#[derive(Debug, Clone)]
pub struct Notification {
    pub message: String,
    pub level: NotificationType,
    pub created_time: Instant,
    pub duration: Duration,
}

impl Notification {
    pub fn new(message: &str, notification_level: NotificationType) -> Self {
        let duration = Self::notification_duration(notification_level);

        Self {
            message: message.to_string(),
            level: notification_level,
            created_time: Instant::now(),
            duration: Duration::from_secs(duration),
        }
    }

    pub fn is_expired(&self) -> bool {
        self.created_time.elapsed() >= self.duration
    }

    fn notification_duration(level: NotificationType) -> u64 {
        match level {
            NotificationType::Error => 10,
            NotificationType::Warning => 7,
            NotificationType::Info => 5,
        }
    }
}

pub struct NotificationManager {
    pub notifications: VecDeque<Notification>,
}

impl NotificationManager {
    const MAX_NOTIFICATION_SIZE: usize = 5;

    pub fn new() -> Self {
        Self {
            notifications: VecDeque::new(),
        }
    }

    pub fn add(&mut self, notification: Notification) {
        self.notifications.push_front(notification);

        if self.notifications.len() > Self::MAX_NOTIFICATION_SIZE {
            self.notifications.pop_back();
        }
    }

    pub fn remove_expired(&mut self) {
        self.notifications.retain(|t| !t.is_expired());
    }
}

impl Widget for &Notification {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let border_style = match self.level {
            NotificationType::Info => Style::default().fg(Color::Green),
            NotificationType::Warning => Style::default().fg(Color::Yellow),
            NotificationType::Error => Style::default().fg(Color::Red),
        };

        let block = Block::default()
            .borders(Borders::ALL)
            .border_style(border_style);

        let paragraph = Paragraph::new(self.message.clone())
            .block(block)
            .wrap(Wrap { trim: true });

        paragraph.render(area, buf);
    }
}

impl Widget for &NotificationManager {
    fn render(self, area: Rect, buf: &mut Buffer) {
        if self.notifications.is_empty() {
            return;
        }

        let [_, right_area] =
            Layout::horizontal([Constraint::Fill(1), Constraint::Percentage(40)]).areas(area);
        let [notifications_area, _] =
            Layout::vertical([Constraint::Fill(1), Constraint::Length(1)]).areas(right_area);

        let mut area_y = notifications_area.y;
        for n in self.notifications.iter() {
            // 最多显示 3 行内容
            let display_content_height = n
                .message
                .width()
                .div_ceil((notifications_area.width - 2) as usize)
                .min(3);
            let display_height = (display_content_height + 2) as u16;
            let n_area = Rect::new(
                notifications_area.x,
                area_y,
                notifications_area.width,
                display_height,
            );

            area_y += display_height;

            if area_y > notifications_area.bottom() {
                break;
            }

            Clear.render(n_area, buf);
            n.render(n_area, buf);
        }
    }
}
