import { InventoryOperations } from "@/features/inventory/operation-state";
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <InventoryOperations>
      <div className="inventory-ui">{children}</div>
    </InventoryOperations>
  );
}
