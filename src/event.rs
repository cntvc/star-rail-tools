use crossterm::event::{self, Event as CrosstermEvent, KeyEvent, MouseEvent};
use futures::{FutureExt, StreamExt};
use tokio::{self, sync::mpsc};

pub enum HsrEvent {
    Tick,
    Key(KeyEvent),
    Mouse(MouseEvent),
    Resize(u16, u16),
    Notice(String),
}

pub fn listen_for_signals(tx: &mpsc::UnboundedSender<HsrEvent>) {
    let local_tx = tx.clone();

    tokio::spawn(async move {
        let tick_rate = std::time::Duration::from_millis(100);
        let mut tick_interval = tokio::time::interval(tick_rate);
        let mut event_stream = event::EventStream::new();

        loop {
            let crossterm_event_next = event_stream.next().fuse();
            let tick_task = tick_interval.tick();

            tokio::select! {
                _ = tick_task => {
                    if local_tx.send(HsrEvent::Tick).is_err(){
                        break;
                    }
                },
                Some(Ok(crossterm_event)) = crossterm_event_next => {
                    let hsr_event = match crossterm_event {
                        CrosstermEvent::Key(key_event) => HsrEvent::Key(key_event),
                        CrosstermEvent::Mouse(mouse) => HsrEvent::Mouse(mouse),
                        CrosstermEvent::Resize(width, height) => HsrEvent::Resize(width, height),
                        _ => continue
                    };
                    if local_tx.send(hsr_event).is_err(){
                        break;
                    }
                },
            }
        }
    });
}
