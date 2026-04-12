import type { TalentProfile } from "@/lib/schemas";
import { buildTalentTodos, type TalentTodo } from "@/components/talents/talent-board-utils";

type TalentTodosProps = {
  talents: TalentProfile[];
};

function priorityLabel(priority: TalentTodo["priority"]) {
  if (priority === "high") {
    return "高优先级";
  }
  if (priority === "medium") {
    return "中优先级";
  }
  return "低优先级";
}

export function TalentTodos({ talents }: TalentTodosProps) {
  const todos = buildTalentTodos(talents).slice(0, 10);

  return (
    <section className="talent-todo-shell">
      <div className="section-header">
        <div>
          <p className="section-kicker">Smart To-Do</p>
          <h3>智能待办</h3>
          <p className="muted-copy">基于达人当前状态自动推荐的下一步行动。</p>
        </div>
      </div>

      {todos.length ? (
        <div className="talent-todo-list">
          {todos.map((todo) => (
            <article
              key={todo.id}
              className={`talent-todo-card talent-todo-${todo.priority}`}
            >
              <div className="talent-todo-topline">
                <span className={`risk-tag talent-todo-priority talent-todo-priority-${todo.priority}`}>
                  {priorityLabel(todo.priority)}
                </span>
                <strong>{todo.talentName}</strong>
              </div>
              <p>{todo.text}</p>
            </article>
          ))}
        </div>
      ) : (
        <article className="empty-state">
          <p>当前所有达人都已经有清晰的下一步动作了，先继续推进现有合作即可。</p>
        </article>
      )}
    </section>
  );
}
