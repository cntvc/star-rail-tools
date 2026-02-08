use crossterm::event::{Event as CrosstermEvent, KeyEvent, KeyEventKind};
use futures::{FutureExt, StreamExt};
use tokio::{self, sync::mpsc::UnboundedSender, task::JoinHandle};

use srt::logger;

#[derive(Clone, Debug)]
pub enum Event {
    Tick,
    Key(KeyEvent),
}

pub struct EventListener {
    task: Option<JoinHandle<()>>,
}

impl EventListener {
    pub fn new() -> Self {
        Self { task: None }
    }

    pub fn start(&mut self, tx: UnboundedSender<Event>) {
        let tick_delay = std::time::Duration::from_millis(250);
        let mut event_reader = crossterm::event::EventStream::new();
        let mut tick_interval = tokio::time::interval(tick_delay);

        self.task = Some(tokio::task::spawn(async move {
            loop {
                tokio::select! {
                    _ = tick_interval.tick() => {
                        if tx.send(Event::Tick).is_err() {
                            break;
                        }
                    }
                    Some(Ok(event)) = event_reader.next().fuse() => {
                        match event {
                            CrosstermEvent::Key(key) if key.kind == KeyEventKind::Release => {
                                logger::trace!("Key: {:?}", key);
                                if tx.send(Event::Key(key)).is_err() {
                                    break;
                                }
                            }
                            _ => {}
                        }
                    }
                }
            }
        }));
    }

    pub fn stop(&mut self) {
        if let Some(task) = self.task.take() {
            task.abort();
        }
    }
}

impl Drop for EventListener {
    fn drop(&mut self) {
        self.stop();
    }
}
