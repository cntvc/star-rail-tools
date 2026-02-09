use crossterm::event::{KeyCode, KeyEvent};
use ratatui::{
    Frame,
    buffer::Buffer,
    layout::{Constraint, Layout, Rect, Spacing},
    style::{Color, Style},
    symbols::merge::MergeStrategy,
    text::Line,
    widgets::{Block, BorderType, Paragraph, Tabs, Widget},
};

use srt::{
    APP_NAME, APP_VERSION,
    core::{GachaAnalysisEntity, GachaType, Metadata},
    logger,
};
use unicode_width::UnicodeWidthStr;

use super::account::AccountListWidget;
use super::import_export::ImportExportWidget;
use super::refresh::RefreshMenuWidget;
use crate::app::{AppModel, FocusNode};
use crate::{
    action::{Action, RouteRequest},
    app,
};
use i18n::I18nKey;

enum Focus {
    Welcome,
    GachaData,
}

pub struct HomeWidget {
    focus: Focus,
    account_menu_widget: AccountListWidget,

    refresh_menu_widget: RefreshMenuWidget,
    import_export_menu_widget: ImportExportWidget,
    gacha_data_widget: GachaDataWidget,
}

impl HomeWidget {
    pub fn new() -> Self {
        Self {
            focus: Focus::Welcome,
            account_menu_widget: AccountListWidget::new(),
            refresh_menu_widget: RefreshMenuWidget::new(),
            import_export_menu_widget: ImportExportWidget::new(),
            gacha_data_widget: GachaDataWidget::new(),
        }
    }

    pub fn render(&mut self, app_model: &mut AppModel, area: Rect, frame: &mut Frame) {
        match app_model.home_mode {
            app::HomeMode::Data => {
                self.focus = Focus::GachaData;
                self.gacha_data_widget.render(app_model, area, frame);
            }
            app::HomeMode::Welcome => {
                self.focus = Focus::Welcome;
                Welcome.render(area, frame);
            }
        }
        match app_model.focus_path.as_slice() {
            [FocusNode::Home, FocusNode::AccountList, ..] => {
                self.account_menu_widget.render(app_model, area, frame)
            }
            [FocusNode::Home, FocusNode::UpdateMenu] => {
                self.refresh_menu_widget.render(area, frame);
            }
            [FocusNode::Home, FocusNode::ImportExportMenu, ..] => {
                self.import_export_menu_widget
                    .render(app_model, area, frame);
            }
            _ => {}
        }
    }

    pub fn handle_key_event(&mut self, key: KeyEvent, focus_path: &[FocusNode]) -> Option<Action> {
        logger::debug!("home widget focus_path: {:?}", focus_path);

        match focus_path {
            [FocusNode::Home] => {
                match key.code {
                    KeyCode::Char('a') | KeyCode::Char('A') => {
                        return Some(Action::Route(RouteRequest::OpenAccountList));
                    }
                    KeyCode::Char('u') | KeyCode::Char('U') => {
                        return Some(Action::Route(RouteRequest::OpenUpdateGachaDataMenu));
                    }
                    KeyCode::Char('d') | KeyCode::Char('D') => {
                        return Some(Action::Route(RouteRequest::OpenImportExportMenu));
                    }
                    _ => {}
                };
                match self.focus {
                    Focus::Welcome => None,
                    Focus::GachaData => self.gacha_data_widget.handle_key_event(key),
                }
            }
            [FocusNode::Home, FocusNode::AccountList, ..] => self
                .account_menu_widget
                .handle_key_event(key, &focus_path[1..]),
            [FocusNode::Home, FocusNode::UpdateMenu] => {
                self.refresh_menu_widget.handle_key_event(key)
            }
            [FocusNode::Home, FocusNode::ImportExportMenu, ..] => self
                .import_export_menu_widget
                .handle_key_event(key, &focus_path[1..]),
            _ => None,
        }
    }
}

struct Welcome;

impl Welcome {
    pub fn render(&self, area: Rect, frame: &mut Frame) {
        let instructions = vec![
            Line::from(format!("{} v{}", APP_NAME, APP_VERSION)),
            Line::from(i18n::loc(I18nKey::TuiHomeWelcomeDesc)),
            Line::from(""),
            Line::from(i18n::loc(I18nKey::TuiHomeWelcomeAddAccount)),
            Line::from(i18n::loc(I18nKey::TuiHomeWelcomeHelp)),
            Line::from(i18n::loc(I18nKey::TuiHomeWelcomeQuit)),
        ];

        let content_height = instructions.len() as u16;
        let inner_area = area.centered(Constraint::Fill(1), Constraint::Length(content_height));
        Paragraph::new(instructions)
            .centered()
            .render(inner_area, frame.buffer_mut());
    }
}

const GACHA_TAB_MAX_COUNT: usize = GachaType::as_array().len();

struct GachaDataWidget {
    /// [srt::core::GachaType::as_array] 顺序的索引
    tab_index: usize,
    scroll_row_offset: [usize; GACHA_TAB_MAX_COUNT],
    max_scroll_offset: [usize; GACHA_TAB_MAX_COUNT],
}

impl GachaDataWidget {
    pub fn new() -> Self {
        Self {
            tab_index: 0,
            scroll_row_offset: [0; GACHA_TAB_MAX_COUNT],
            max_scroll_offset: [0; GACHA_TAB_MAX_COUNT],
        }
    }

    pub fn handle_key_event(&mut self, key: KeyEvent) -> Option<Action> {
        match key.code {
            KeyCode::Left => {
                self.prev_tab();
                None
            }
            KeyCode::Right => {
                self.next_tab();
                None
            }
            KeyCode::Down => {
                self.scroll_down(1);
                None
            }
            KeyCode::Up => {
                self.scroll_up(1);
                None
            }
            _ => None,
        }
    }

    fn scroll_down(&mut self, lines: usize) {
        self.scroll_row_offset[self.tab_index] = self.scroll_row_offset[self.tab_index]
            .saturating_add(lines)
            .min(self.max_scroll_offset[self.tab_index]);
    }

    fn scroll_up(&mut self, lines: usize) {
        self.scroll_row_offset[self.tab_index] =
            self.scroll_row_offset[self.tab_index].saturating_sub(lines);
    }

    fn next_tab(&mut self) {
        self.tab_index = (self.tab_index + 1) % GACHA_TAB_MAX_COUNT;
    }

    fn prev_tab(&mut self) {
        self.tab_index = (self.tab_index + GACHA_TAB_MAX_COUNT - 1) % GACHA_TAB_MAX_COUNT;
    }

    pub fn render(&mut self, app_model: &AppModel, area: Rect, frame: &mut Frame) {
        let [tab_area, header_area, grid_area] = Layout::vertical([
            Constraint::Length(2), // Tab栏
            Constraint::Length(3), // Header汇总区
            Constraint::Fill(1),   // Grid卡片区
        ])
        .areas(area);

        let gacha_type_array = GachaType::as_array().map(|i| i as u8);
        let gacha_type = gacha_type_array[self.tab_index];

        self.render_tabs(self.tab_index, tab_area, frame.buffer_mut());

        let analysis = app_model.gacha_analysis.get(&gacha_type);
        self.render_header(analysis, header_area, frame.buffer_mut());

        if let Some(analysis) = analysis {
            let max_name_width = self.calc_max_name_width(app_model);
            self.render_grid(
                analysis,
                &app_model.metadata,
                max_name_width,
                grid_area,
                frame.buffer_mut(),
            );
        }
    }

    fn render_tabs(&self, tab_index: usize, area: Rect, buf: &mut Buffer) {
        let [tab_line_area, separator_area] =
            Layout::vertical([Constraint::Length(1), Constraint::Length(1)]).areas(area);

        let tabs_name = GachaType::as_array()
            .iter()
            .map(|gacha_type| gacha_type_name(*gacha_type))
            .collect::<Vec<&str>>();

        Tabs::new(tabs_name)
            .style(Color::DarkGray)
            .highlight_style(Style::default().white().on_black().bold())
            .select(tab_index)
            .divider("|")
            .render(tab_line_area, buf);

        let separator = "─".repeat(separator_area.width.saturating_sub(2) as usize);
        Paragraph::new(separator)
            .style(Style::default().fg(Color::DarkGray))
            .centered()
            .render(separator_area, buf);
    }

    fn render_header(&self, analysis: Option<&GachaAnalysisEntity>, area: Rect, buf: &mut Buffer) {
        if analysis.is_none() {
            return;
        }
        let analysis = analysis.unwrap();
        let total_count = analysis.total_count;
        let rank5_count = analysis.rank5.len();
        let avg_pity = if rank5_count > 0 {
            analysis
                .rank5
                .iter()
                .map(|p| p.pull_index as f32)
                .sum::<f32>()
                / rank5_count as f32
        } else {
            0.0
        };

        let [total_count_area, rank5_count_area, avg_pity_area] = Layout::horizontal([
            Constraint::Fill(1),
            Constraint::Fill(1),
            Constraint::Fill(1),
        ])
        .spacing(Spacing::Overlap(1))
        .areas(area);

        let block = Block::bordered()
            .border_type(BorderType::Plain)
            .merge_borders(MergeStrategy::Exact)
            .border_style(Style::default().fg(Color::DarkGray));

        // 渲染总抽数区域
        let inner = block.inner(total_count_area);
        block.clone().render(total_count_area, buf);
        Paragraph::new(format!(
            "{}: {}",
            i18n::loc(I18nKey::TuiGachaTotalPulls),
            total_count
        ))
        .centered()
        .style(Style::default().fg(Color::White))
        .render(inner, buf);

        // 渲染五星数区域
        let inner = block.inner(rank5_count_area);
        block.clone().render(rank5_count_area, buf);
        Paragraph::new(format!(
            "{}: {}",
            i18n::loc(I18nKey::TuiGachaRank5Count),
            rank5_count
        ))
        .centered()
        .style(Style::default().fg(Color::White))
        .render(inner, buf);

        // 渲染平均抽数区域

        let inner = block.inner(avg_pity_area);
        block.render(avg_pity_area, buf);
        Paragraph::new(format!(
            "{}: {:.1}",
            i18n::loc(I18nKey::TuiGachaAvgPity),
            avg_pity
        ))
        .centered()
        .style(Style::default().fg(Color::White))
        .render(inner, buf);
    }

    fn render_grid(
        &mut self,
        analysis: &GachaAnalysisEntity,
        metadata: &Metadata,
        max_name_width: usize,
        area: Rect,
        buf: &mut Buffer,
    ) {
        /*  cell 宽度30 - 40
            name 区域 遍历所有 item 的 name，取最长
            边框 2
            抽数 "★ {pity_count}" 固定4字符长
            序号 "{seq}. " 最少4字符长
        */
        let cell_width = (max_name_width + 10).clamp(30, 40);
        let (cols, rows) = self.calc_grid_size(area, cell_width, analysis);

        const ROW_HEIGHT: u16 = 3;
        // +1 是追加底部无缝裁剪的一行
        let visible_rows = area.height as usize / (ROW_HEIGHT as usize - 1) + 1;

        // 更新最大滚动偏移量
        self.max_scroll_offset[self.tab_index] = rows.saturating_sub(visible_rows) + 1;

        let start_row = self.scroll_row_offset[self.tab_index];
        let end_row = (start_row + visible_rows).min(rows);

        let col_constraints = (0..cols).map(|_| Constraint::Fill(1));
        let row_constraints = (start_row..end_row).map(|_| Constraint::Length(ROW_HEIGHT));

        let horizontal = Layout::horizontal(col_constraints).spacing(Spacing::Overlap(1));
        let vertical = Layout::vertical(row_constraints).spacing(Spacing::Overlap(1));

        // 虚拟 buffer
        let virtual_area = Rect {
            x: 0,
            y: 0,
            width: area.width,
            height: visible_rows as u16 * (ROW_HEIGHT - 1) + 1,
        };
        let mut virtual_buf = Buffer::empty(virtual_area);

        let cells = virtual_area
            .layout_vec(&vertical)
            .iter()
            .flat_map(|row| row.layout_vec(&horizontal))
            .collect::<Vec<_>>();
        let total_count = analysis.rank5.len() + 1;

        // 第一行时，第一个 cell 绘制保底计数
        if start_row == 0 {
            self.render_card(
                cells[0],
                total_count,
                i18n::loc(I18nKey::TuiGachaPityCounter),
                analysis.pity_count,
                &mut virtual_buf,
            );
        }

        // 需绘制的 rank5 起始索引
        let rank5_start_idx = if start_row == 0 {
            0 // 第一行从 rank5[0] 开始
        } else {
            start_row * cols - 1 // 后续行减去保底计数占据的1个位置
        };

        // 遍历剩余的 cells（第一行跳过第一个）
        let cells_iter = if start_row == 0 {
            cells.iter().skip(1)
        } else {
            cells.iter().skip(0)
        };

        let rank5_rev = analysis.rank5.iter().rev().collect::<Vec<_>>();
        for (offset, cell_area) in cells_iter.enumerate() {
            // rank5 在 analysis.rank5 的索引
            let rank5_idx = rank5_start_idx + offset;
            if rank5_idx < rank5_rev.len() {
                let item = rank5_rev[rank5_idx];
                let seq = total_count - 1 - rank5_idx;
                let name = metadata.get_item_name(item.item_id, i18n::lang());
                // 未查询到name时，使用id
                let name = name
                    .and_then(|name| Some(name.to_string()))
                    .unwrap_or(format!("{}", item.id));

                self.render_card(*cell_area, seq, &name, item.pull_index, &mut virtual_buf);
            } else {
                break;
            }
        }

        // 将虚拟 buffer 渲染到实际的 buffer
        for y in 0..virtual_area.height {
            let dst_y = y + area.y;
            if dst_y >= area.bottom() {
                break;
            }

            for x in 0..virtual_area.width {
                let dst_x = x + area.x;
                if dst_x >= area.right() {
                    break;
                }

                if let Some(cell) = virtual_buf.cell((x, y)) {
                    buf[(dst_x, dst_y)] = cell.clone();
                }
            }
        }
    }

    fn render_card(&self, area: Rect, seq: usize, name: &str, pull_count: u8, buf: &mut Buffer) {
        let card_block = Block::bordered()
            .border_type(BorderType::Plain)
            .merge_borders(MergeStrategy::Exact)
            .border_style(Style::default().fg(Color::DarkGray));
        let card_inner = card_block.inner(area);
        card_block.render(area, buf);

        let [left_text, right_text] =
            Layout::horizontal([Constraint::Fill(1), Constraint::Length(4)]).areas(card_inner);
        Paragraph::new(format!("{}. {}", seq, name)).render(left_text, buf);
        Paragraph::new(format!("★ {}", pull_count))
            .right_aligned()
            .render(right_text, buf);
    }

    fn calc_grid_size(
        &self,
        area: Rect,
        cell_width: usize,
        analysis: &GachaAnalysisEntity,
    ) -> (usize, usize) {
        // 最少绘制一列
        // -1 是因为 border 重合，相当于各个方向上单个 cell 只占1条 border
        let col_count = ((area.width as usize - 1) / (cell_width - 1)).max(1);
        // +1 是保底计数 cell
        let total_cells = analysis.rank5.len() + 1;
        // 向上取整
        let row_count = total_cells.div_ceil(col_count);
        (col_count, row_count)
    }

    /// 计算name的最大宽度
    fn calc_max_name_width(&self, app_model: &AppModel) -> usize {
        let mut max_name_len = 0;
        for (_, i) in app_model.gacha_analysis.iter() {
            for rank5 in i.rank5.iter() {
                if let Some(name) = app_model
                    .metadata
                    .get_item_name(rank5.item_id, i18n::lang())
                {
                    max_name_len = max_name_len.max(name.width());
                }
            }
        }
        max_name_len
    }
}

pub fn gacha_type_name(gacha_type: GachaType) -> &'static str {
    match gacha_type as u8 {
        1 => i18n::loc(i18n::I18nKey::RegularWarp),
        2 => i18n::loc(i18n::I18nKey::StarterWarp),
        11 => i18n::loc(i18n::I18nKey::CharacterEventWarp),
        12 => i18n::loc(i18n::I18nKey::LightConeEventWarp),
        21 => i18n::loc(i18n::I18nKey::CharacterCollaborationWarp),
        22 => i18n::loc(i18n::I18nKey::LightConeCollaborationWarp),
        _ => unreachable!(),
    }
}
