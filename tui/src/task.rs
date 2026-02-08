use std::collections::HashMap;
use std::fmt::Display;
use std::future::Future;

use tokio::sync::mpsc::UnboundedSender;
use tokio_util::sync::CancellationToken;

use crate::action::{Action, TaskAction};
use srt::{AppError, logger};

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct TaskId(String);

impl TaskId {
    fn new(name: &str, group: TaskGroupId) -> Self {
        Self(format!("{}:{}", name, group.to_string()))
    }
}

impl Display for TaskId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash, Copy)]
pub enum TaskGroupId {
    Global,
    User,
}

impl TaskGroupId {
    fn to_string(&self) -> String {
        match self {
            TaskGroupId::Global => "Global".to_string(),
            TaskGroupId::User => "User".to_string(),
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
pub enum TaskStatus {
    Pending,
    Running,
    Completed,
    Cancelled,
    Failed,
}

#[derive(Debug)]
pub struct Task {
    pub id: TaskId,
    pub group: TaskGroupId,
    pub name: String,
    pub status: TaskStatus,
    pub visible: bool,
    pub description: String,
    pub(crate) cancel_token: CancellationToken,
}

impl Task {
    fn new(
        id: TaskId,
        group: TaskGroupId,
        name: String,
        visible: bool,
        description: String,
    ) -> Self {
        Self {
            id,
            group,
            name,
            status: TaskStatus::Pending,
            visible,
            description,
            cancel_token: CancellationToken::new(),
        }
    }

    pub fn is_finished(&self) -> bool {
        matches!(
            self.status,
            TaskStatus::Completed | TaskStatus::Cancelled | TaskStatus::Failed
        )
    }
}

pub struct TaskManager {
    tasks: HashMap<TaskId, Task>,
    action_tx: UnboundedSender<Action>,
}

impl TaskManager {
    pub fn new(action_tx: UnboundedSender<Action>) -> Self {
        Self {
            tasks: HashMap::new(),
            action_tx,
        }
    }

    pub fn start<F>(
        &mut self,
        name: impl Into<String>,
        group: TaskGroupId,
        visible: bool,
        description: impl Into<String>,
        fut: F,
    ) -> Option<TaskId>
    where
        F: Future<Output = Result<(), AppError>> + Send + 'static,
    {
        let task_name = name.into();
        let task_id = TaskId::new(&task_name, group);

        // 检查任务是否已存在
        if self.tasks.contains_key(&task_id) {
            logger::warn!(
                "task already exists, name: {} group: {:?}",
                task_name,
                group
            );
            return None;
        }

        let mut task = Task::new(
            task_id.clone(),
            group,
            task_name.clone(),
            visible,
            description.into(),
        );
        let cancel_token = task.cancel_token.clone();
        task.status = TaskStatus::Running;
        logger::debug!("task start, id: {} name: {}", task.id, task.name);

        self.tasks.insert(task_id.clone(), task);
        let tx = self.action_tx.clone();
        let _ = tx.send(Action::Task(TaskAction::Started(task_id.clone())));

        let task_id_for_spawn = task_id.clone();
        tokio::spawn(async move {
            tokio::select! {
                r = fut => {
                    match r {
                        Ok(()) => {
                            let _ = tx.send(Action::Task(TaskAction::Completed(task_id_for_spawn)));
                        }
                        Err(e) => {
                            let _ = tx.send(Action::Task(TaskAction::Failed(task_id_for_spawn, e)));
                        }
                    }
                },
                _ = cancel_token.cancelled() => {
                    let _ = tx.send(Action::Task(TaskAction::Cancelled(task_id_for_spawn)));
                    return;
                },
            };
        });

        Some(task_id)
    }

    pub fn cancel_group(&mut self, group: TaskGroupId) {
        for task in self.tasks.values() {
            if task.group == group {
                task.cancel_token.cancel();
            }
        }
    }

    pub fn cancel_all(&mut self) {
        for task in self.tasks.values() {
            task.cancel_token.cancel();
        }
    }

    pub fn cancel(&mut self, task_id: &TaskId) {
        if let Some(task) = self.tasks.get_mut(task_id) {
            task.cancel_token.cancel();
            task.status = TaskStatus::Cancelled;
        }
    }

    pub fn get_task(&mut self, task_id: &TaskId) -> Option<&mut Task> {
        self.tasks.get_mut(task_id)
    }

    pub fn cleanup_finished(&mut self) {
        self.tasks.retain(|_, task| !task.is_finished());
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio::sync::mpsc;
    use tokio::time::{Duration, sleep};

    #[tokio::test]
    async fn test_task_id_increment() {
        let (tx, _rx) = mpsc::unbounded_channel();
        let mut manager = TaskManager::new(tx);

        let id1 = manager
            .start("task1", TaskGroupId::Global, false, "".to_string(), async {
                Ok(())
            })
            .expect("task1 should start");
        let id2 = manager
            .start("task2", TaskGroupId::Global, false, "".to_string(), async {
                Ok(())
            })
            .expect("task2 should start");

        assert_ne!(id1, id2);
    }

    #[tokio::test]
    async fn test_task_start_and_complete() {
        let (tx, mut rx) = mpsc::unbounded_channel();
        let mut manager = TaskManager::new(tx);

        let task_id = manager
            .start(
                "test_task",
                TaskGroupId::Global,
                false,
                "".to_string(),
                async { Ok(()) },
            )
            .expect("task should start");

        if let Some(Action::Task(TaskAction::Started(id))) = rx.recv().await {
            assert_eq!(id, task_id);
        } else {
            panic!("Expected Started action");
        }

        if let Some(Action::Task(TaskAction::Completed(id))) = rx.recv().await {
            assert_eq!(id, task_id);
        } else {
            panic!("Expected Completed action");
        }
    }

    #[tokio::test]
    async fn test_task_cancel() {
        let (tx, mut rx) = mpsc::unbounded_channel();
        let mut manager = TaskManager::new(tx);

        let task_id = manager
            .start(
                "test_task",
                TaskGroupId::Global,
                false,
                "".to_string(),
                async {
                    sleep(Duration::from_secs(10)).await;
                    Ok(())
                },
            )
            .expect("task should start");

        let _ = rx.recv().await;

        manager.cancel(&task_id);

        if let Some(Action::Task(TaskAction::Cancelled(id))) = rx.recv().await {
            assert_eq!(id, task_id);
        } else {
            panic!("Expected Cancelled action");
        }
    }

    #[tokio::test]
    async fn test_cancel_group() {
        let (tx, mut rx) = mpsc::unbounded_channel();
        let mut manager = TaskManager::new(tx);

        let id1 = manager
            .start("task1", TaskGroupId::User, false, "".to_string(), async {
                sleep(Duration::from_secs(10)).await;
                Ok(())
            })
            .expect("task1 should start");
        let id2 = manager
            .start("task2", TaskGroupId::User, false, "".to_string(), async {
                sleep(Duration::from_secs(10)).await;
                Ok(())
            })
            .expect("task2 should start");

        let _ = rx.recv().await;
        let _ = rx.recv().await;

        manager.cancel_group(TaskGroupId::User);

        let mut cancelled_ids = Vec::new();
        for _ in 0..2 {
            if let Some(Action::Task(TaskAction::Cancelled(id))) = rx.recv().await {
                cancelled_ids.push(id);
            }
        }

        assert!(cancelled_ids.contains(&id1));
        assert!(cancelled_ids.contains(&id2));
    }

    #[test]
    fn test_task_is_finished() {
        let task_id = TaskId::new("test", TaskGroupId::Global);
        let task = Task::new(
            task_id,
            TaskGroupId::Global,
            "test".to_string(),
            false,
            "".to_string(),
        );
        assert!(!task.is_finished()); // Pending

        let mut task = task;
        task.status = TaskStatus::Running;
        assert!(!task.is_finished());

        task.status = TaskStatus::Completed;
        assert!(task.is_finished());

        task.status = TaskStatus::Cancelled;
        assert!(task.is_finished());

        task.status = TaskStatus::Failed;
        assert!(task.is_finished());
    }

    #[tokio::test]
    async fn test_cleanup_finished() {
        let (tx, _rx) = mpsc::unbounded_channel();
        let mut manager = TaskManager::new(tx);

        let task1_id = TaskId::new("task1", TaskGroupId::Global);
        let mut task1 = Task::new(
            task1_id.clone(),
            TaskGroupId::Global,
            "task1".to_string(),
            false,
            "".to_string(),
        );
        task1.status = TaskStatus::Completed;

        let task2_id = TaskId::new("task2", TaskGroupId::Global);
        let mut task2 = Task::new(
            task2_id.clone(),
            TaskGroupId::Global,
            "task2".to_string(),
            false,
            "".to_string(),
        );
        task2.status = TaskStatus::Running;

        let task3_id = TaskId::new("task3", TaskGroupId::Global);
        let mut task3 = Task::new(
            task3_id.clone(),
            TaskGroupId::Global,
            "task3".to_string(),
            false,
            "".to_string(),
        );
        task3.status = TaskStatus::Failed;

        manager.tasks.insert(task1_id, task1);
        manager.tasks.insert(task2_id, task2);
        manager.tasks.insert(task3_id, task3);

        assert_eq!(manager.tasks.len(), 3);

        manager.cleanup_finished();

        assert_eq!(manager.tasks.len(), 1);
        assert_eq!(
            manager.tasks.values().next().unwrap().status,
            TaskStatus::Running
        );
    }
}
