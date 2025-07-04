use crossterm::event::KeyCode;
use ratatui::Frame;
use tokio::sync::mpsc;

use crate::Result;
use crate::event::HsrEvent;

pub struct App {
    exit: bool,
    tx: mpsc::UnboundedSender<HsrEvent>,
    rx: mpsc::UnboundedReceiver<HsrEvent>,
}

impl App {
    pub fn new() -> App {
        let (tx, rx) = mpsc::unbounded_channel::<HsrEvent>();
        App {
            exit: false,
            tx,
            rx,
        }
    }

    pub async fn run(&mut self, terminal: &mut ratatui::DefaultTerminal) -> Result<()> {
        crate::event::listen_for_signals(&self.tx);

        while !self.exit {
            terminal.draw(|frame| self.draw(frame))?;
            match self.rx.recv().await {
                Some(event) => {
                    self.update(event);
                }
                None => {
                    break;
                }
            };
        }

        Ok(())
    }

    fn draw(&self, frame: &mut Frame) {}

    pub fn update(&mut self, event: HsrEvent) {
        match event {
            HsrEvent::Key(key_event) => match key_event.code {
                KeyCode::Char('q') => self.exit(),
                _ => {}
            },
            _ => {}
        }
    }

    fn exit(&mut self) {
        self.exit = true;
    }
}
