import { render, screen } from "@testing-library/react";
import { it, expect } from "vitest";
import { DataTable, Input, Textarea, Pagination } from "@/components/ui";
it("escapes API text instead of executing Management HTML", () => {
  render(
    <DataTable
      rows={[{ id: "synthetic", label: "<img src=x onerror=alert(1)>" }]}
      rowKey={(r) => r.id}
      label="Results"
      columns={[{ label: "Name", cell: (r) => r.label }]}
    />,
  );
  expect(screen.getByText("<img src=x onerror=alert(1)>")).toBeVisible();
  expect(document.querySelector("img")).toBeNull();
  expect(screen.getByRole("columnheader")).toHaveAttribute("scope", "col");
});
it("associates input validation and descriptions accessibly", () => {
  render(
    <>
      <Input label="Title" error="Required" hint="Synthetic only" />
      <Textarea label="Description" error="Invalid" />
    </>,
  );
  expect(screen.getByLabelText("Title")).toHaveAttribute(
    "aria-invalid",
    "true",
  );
  expect(screen.getByLabelText("Title")).toHaveAccessibleDescription(
    "Synthetic only Required",
  );
  expect(screen.getByLabelText("Description")).toHaveAccessibleDescription(
    "Invalid",
  );
});
it("keeps next page available when the API does not provide total", () => {
  render(<Pagination offset={50} size={50} onChange={() => {}} />);
  expect(screen.getByRole("button", { name: "Siguiente" })).toBeEnabled();
});
