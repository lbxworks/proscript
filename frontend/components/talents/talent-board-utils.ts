import type { TalentMutationRequest, TalentProfile } from "@/lib/schemas";

export type TalentStageKey = "pending" | "contacting" | "signed" | "producing" | "done";
export type TalentTodoPriority = "high" | "medium" | "low";

export type TalentBoardColumn = {
  key: TalentStageKey;
  title: string;
  color: string;
  defaultProgress: string;
  matches: string[];
};

export type TalentTodo = {
  id: string;
  talentId: number;
  talentName: string;
  priority: TalentTodoPriority;
  text: string;
};

export const TALENT_BOARD_COLUMNS: TalentBoardColumn[] = [
  {
    key: "pending",
    title: "待沟通",
    color: "#9CA3AF",
    defaultProgress: "待沟通",
    matches: ["待沟通"],
  },
  {
    key: "contacting",
    title: "沟通中",
    color: "#3B82F6",
    defaultProgress: "沟通中",
    matches: ["跟进", "对接", "沟通"],
  },
  {
    key: "signed",
    title: "已签约",
    color: "var(--accent)",
    defaultProgress: "已签约",
    matches: ["推进", "签约", "已签"],
  },
  {
    key: "producing",
    title: "内容制作",
    color: "#8B5CF6",
    defaultProgress: "内容制作",
    matches: ["制作", "拍摄", "创作"],
  },
  {
    key: "done",
    title: "已完成",
    color: "var(--success)",
    defaultProgress: "已完成",
    matches: ["已合作", "完成", "交付"],
  },
];

export function resolveTalentStageKey(progress: string | null | undefined): TalentStageKey {
  const normalized = String(progress || "").trim();

  for (const column of TALENT_BOARD_COLUMNS) {
    if (column.matches.some((keyword) => normalized.includes(keyword))) {
      return column.key;
    }
  }

  return "pending";
}

export function getTalentBoardColumn(stageKey: TalentStageKey): TalentBoardColumn {
  return TALENT_BOARD_COLUMNS.find((column) => column.key === stageKey) || TALENT_BOARD_COLUMNS[0];
}

export function buildTalentMutationPayload(
  talent: TalentProfile,
  overrides: Partial<TalentMutationRequest> = {},
): TalentMutationRequest {
  return {
    name: talent.name,
    platform: talent.platform || "未设置",
    email: talent.email || "",
    recent_video_link: talent.recent_video_link || "",
    notes: talent.notes || "",
    collaboration_progress: talent.collaboration_progress || "待沟通",
    ...overrides,
  };
}

function makeTodo(
  talent: TalentProfile,
  priority: TalentTodoPriority,
  text: string,
): TalentTodo {
  return {
    id: `${priority}-${talent.id}-${text}`,
    talentId: talent.id,
    talentName: talent.name,
    priority,
    text,
  };
}

function priorityRank(priority: TalentTodoPriority): number {
  if (priority === "high") {
    return 0;
  }
  if (priority === "medium") {
    return 1;
  }
  return 2;
}

export function buildTalentTodos(talents: TalentProfile[]): TalentTodo[] {
  const todos: TalentTodo[] = [];

  for (const talent of talents) {
    const stage = resolveTalentStageKey(talent.collaboration_progress);

    if (stage === "pending") {
      if (!talent.email.trim()) {
        todos.push(makeTodo(talent, "high", `补充达人「${talent.name}」的联系邮箱`));
      } else {
        todos.push(makeTodo(talent, "medium", `发送合作意向邮件给「${talent.name}」`));
      }
      continue;
    }

    if (stage === "contacting") {
      if (!talent.recent_video_link.trim()) {
        todos.push(makeTodo(talent, "medium", `收集「${talent.name}」的近期代表作链接`));
      } else {
        todos.push(makeTodo(talent, "medium", `与「${talent.name}」确认合作条款并推进签约`));
      }
      continue;
    }

    if (stage === "signed") {
      if (!talent.notes.trim()) {
        todos.push(makeTodo(talent, "medium", `为「${talent.name}」补充创作风格备注`));
      } else {
        todos.push(makeTodo(talent, "high", `启动「${talent.name}」的脚本生成任务`));
      }
      continue;
    }

    if (stage === "producing") {
      todos.push(makeTodo(talent, "medium", `跟进「${talent.name}」的拍摄进度并确认交付日期`));
      continue;
    }

    todos.push(makeTodo(talent, "low", `「${talent.name}」合作已完成，可考虑二次合作`));
  }

  return todos.sort((left, right) => {
    const priorityDiff = priorityRank(left.priority) - priorityRank(right.priority);
    if (priorityDiff !== 0) {
      return priorityDiff;
    }
    return left.talentName.localeCompare(right.talentName, "zh-CN");
  });
}
