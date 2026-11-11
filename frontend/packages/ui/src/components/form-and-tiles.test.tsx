import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CheckList, Field, Input, TileGroup } from "../index";

describe("Field", () => {
  it("links label, control and error for assistive tech", () => {
    render(
      <Field label="Host" error="Host is required" required>
        {(p) => <Input {...p} />}
      </Field>,
    );
    const input = screen.getByLabelText(/Host/);
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription("Host is required");
  });
});

describe("TileGroup", () => {
  const options = [
    { value: "postgres", label: "Postgres" },
    { value: "mysql", label: "MySQL" },
    { value: "oracle", label: "Oracle", disabled: true },
  ];

  it("selects on click and exposes radio semantics", () => {
    const onChange = vi.fn();
    render(<TileGroup aria-label="Engine" options={options} value="postgres" onChange={onChange} />);
    expect(screen.getByRole("radio", { name: "Postgres" })).toHaveAttribute("aria-checked", "true");
    fireEvent.click(screen.getByRole("radio", { name: "MySQL" }));
    expect(onChange).toHaveBeenCalledWith("mysql");
  });

  it("moves with arrow keys and skips disabled options", () => {
    const onChange = vi.fn();
    render(<TileGroup aria-label="Engine" options={options} value="mysql" onChange={onChange} />);
    fireEvent.keyDown(screen.getByRole("radiogroup"), { key: "ArrowRight" });
    expect(onChange).toHaveBeenCalledWith("postgres");
  });
});

describe("CheckList", () => {
  it("renders each check with its status and a fix button when available", () => {
    render(
      <CheckList
        items={[
          { name: "Reachable", status: "ok", detail: "PostgreSQL 17 · 3 ms" },
          { name: "Change tracking", status: "warning", fixScript: "ALTER SYSTEM ..." },
        ]}
      />,
    );
    const rows = screen.getAllByRole("listitem");
    expect(rows.map((r) => r.dataset.status)).toEqual(["ok", "warning"]);
    expect(screen.getByRole("button", { name: /Copy fix/ })).toBeInTheDocument();
  });
});
