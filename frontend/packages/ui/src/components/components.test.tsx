import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  Button,
  DataTable,
  ProgressBar,
  SegmentedTabs,
  StatusBadge,
  Stepper,
  type Column,
} from "../index";

describe("Button", () => {
  it("defaults to type=button so it never submits forms by accident", () => {
    render(<Button>Save</Button>);
    expect(screen.getByRole("button", { name: "Save" })).toHaveAttribute("type", "button");
  });

  it("applies the primary variant", () => {
    render(<Button variant="primary">Go</Button>);
    expect(screen.getByRole("button")).toHaveClass("bg-ink");
  });
});

describe("StatusBadge", () => {
  it("exposes its tone for styling and tests", () => {
    render(<StatusBadge tone="warning">Awaiting approval</StatusBadge>);
    expect(screen.getByText("Awaiting approval")).toHaveAttribute("data-tone", "warning");
  });
});

describe("ProgressBar", () => {
  it("clamps values and reports them accessibly", () => {
    render(<ProgressBar value={140} label="Copy progress" />);
    expect(screen.getByRole("progressbar", { name: "Copy progress" })).toHaveAttribute(
      "aria-valuenow",
      "100",
    );
  });
});

describe("Stepper", () => {
  it("marks earlier steps done and the current step", () => {
    const steps = [
      { id: "connect", label: "Connect" },
      { id: "check", label: "Check" },
      { id: "settings", label: "Settings" },
    ];
    render(<Stepper steps={steps} current="check" />);
    const items = screen.getAllByRole("listitem");
    expect(items.map((li) => li.dataset.state)).toEqual(["done", "current", "todo"]);
    expect(items[1]).toHaveAttribute("aria-current", "step");
  });
});

describe("DataTable", () => {
  type Row = { id: string; name: string };
  const columns: Column<Row>[] = [{ id: "name", header: "Name", cell: (r) => r.name }];

  it("renders rows and handles clicks", () => {
    const onRowClick = vi.fn();
    render(
      <DataTable
        columns={columns}
        rows={[{ id: "1", name: "billing-db" }]}
        rowKey={(r) => r.id}
        onRowClick={onRowClick}
      />,
    );
    fireEvent.click(screen.getByText("billing-db"));
    expect(onRowClick).toHaveBeenCalledWith({ id: "1", name: "billing-db" });
  });

  it("shows the empty state", () => {
    render(<DataTable columns={columns} rows={[]} rowKey={(r) => r.id} empty="No migrations" />);
    expect(screen.getByText("No migrations")).toBeInTheDocument();
  });
});

describe("SegmentedTabs", () => {
  it("selects tabs", () => {
    const onChange = vi.fn();
    render(
      <SegmentedTabs
        tabs={[
          { id: "all", label: "All", count: 24 },
          { id: "running", label: "Running", count: 5 },
        ]}
        value="all"
        onChange={onChange}
      />,
    );
    expect(screen.getByRole("tab", { name: /All/ })).toHaveAttribute("aria-selected", "true");
    fireEvent.click(screen.getByRole("tab", { name: /Running/ }));
    expect(onChange).toHaveBeenCalledWith("running");
  });
});
