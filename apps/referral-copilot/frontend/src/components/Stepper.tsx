export function Stepper({ current, labels }: { current: number; labels: string[] }) {
  return (
    <div className="stepper">
      {labels.map((label, index) => {
        const state = index < current ? "done" : index === current ? "active" : "";
        const mark = state === "done" ? "✓ " : `${index + 1}. `;
        return (
          <div className={`step ${state}`} key={label}>
            {mark}
            {label}
          </div>
        );
      })}
    </div>
  );
}
