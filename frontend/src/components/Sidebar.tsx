import { NavLink } from "react-router-dom";
import {
  Home as HomeIcon,
  Wallet,
  ReceiptText,
  PiggyBank,
  LineChart,
  User2,
} from "lucide-react";

const items = [
  { to: "/home", label: "Home", Icon: HomeIcon },
  { to: "/accounts", label: "Accounts", Icon: Wallet },
  { to: "/transactions", label: "Transactions", Icon: ReceiptText },
  { to: "/budget", label: "Budget", Icon: PiggyBank },
  { to: "/insights", label: "Insights", Icon: LineChart },
  { to: "/profile", label: "Profile", Icon: User2 },
];

export default function Sidebar() {
  return (
    <aside className="sticky top-0 hidden h-screen w-20 flex-col items-center gap-3 border-r border-gray-200 bg-white/80 py-4 backdrop-blur md:flex">
      {items.map(({ to, label, Icon }) => (
        <NavLink
          key={to}
          to={to}
          title={label}
          className={({ isActive }) =>
            `group relative grid h-12 w-12 place-items-center rounded-xl transition
             ${isActive
               ? "bg-indigo-50 text-indigo-600 ring-1 ring-indigo-200"
               : "text-gray-500 hover:bg-indigo-50 hover:text-indigo-600"}`
          }
        >
          <Icon className="h-5 w-5" />
          <span className="pointer-events-none absolute left-20 hidden rounded-md bg-gray-900 px-2 py-1 text-xs text-white shadow-md group-hover:block lg:block lg:opacity-0 lg:group-hover:opacity-100">
            {label}
          </span>
        </NavLink>
      ))}
    </aside>
  );
}
