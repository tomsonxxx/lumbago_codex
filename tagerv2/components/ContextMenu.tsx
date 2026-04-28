import React, { useEffect, useRef, useState } from "react";

export interface ContextMenuAction {
  label: string;
  icon?: React.ReactNode;
  onClick: () => void;
  isDanger?: boolean;
  divider?: boolean;
  disabled?: boolean;
  subMenu?: ContextMenuAction[]; // New: Support for nested menus
}

interface ContextMenuProps {
  x: number;
  y: number;
  actions: ContextMenuAction[];
  onClose: () => void;
}

const ContextMenu: React.FC<ContextMenuProps> = ({
  x,
  y,
  actions,
  onClose,
}) => {
  const menuRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState({ x, y });
  const [activeSubMenuIndex, setActiveSubMenuIndex] = useState<number | null>(
    null,
  );

  useEffect(() => {
    // Adjust position if it flows out of the screen
    if (menuRef.current) {
      const { offsetWidth, offsetHeight } = menuRef.current;
      let newX = x;
      let newY = y;

      if (x + offsetWidth > window.innerWidth) {
        newX = window.innerWidth - offsetWidth - 10;
      }
      if (y + offsetHeight > window.innerHeight) {
        newY = window.innerHeight - offsetHeight - 10;
      }
      setPosition({ x: newX, y: newY });
    }
  }, [x, y]);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    const handleScroll = () => onClose();

    document.addEventListener("mousedown", handleClick);
    window.addEventListener("scroll", handleScroll, true);

    return () => {
      document.removeEventListener("mousedown", handleClick);
      window.removeEventListener("scroll", handleScroll, true);
    };
  }, [onClose]);

  return (
    <div
      ref={menuRef}
      style={{ top: position.y, left: position.x }}
      className="fixed z-50 min-w-[220px] bg-[var(--bg-surface)] dark:bg-[var(--bg-panel)] rounded-none shadow-xl border border-[var(--border-color)] dark:border-[var(--border-color)] py-1 animate-fade-in-up"
    >
      {actions.map((action, index) => (
        <React.Fragment key={index}>
          {action.divider && (
            <div className="my-1 border-t border-[var(--border-color)] dark:border-[var(--border-color)]" />
          )}

          <div
            className="relative"
            onMouseEnter={() => setActiveSubMenuIndex(index)}
            onMouseLeave={() => setActiveSubMenuIndex(null)}
          >
            <button
              onClick={() => {
                if (!action.subMenu) {
                  action.onClick();
                  onClose();
                }
              }}
              disabled={action.disabled}
              className={`w-full text-left px-4 py-2 text-sm flex items-center justify-between hover:bg-[var(--bg-panel)] dark:hover:bg-[var(--bg-panel)] transition-colors
                        ${action.isDanger ? "text-red-600 dark:text-red-400" : "text-[var(--text-secondary)] dark:text-[var(--text-secondary)]"}
                        ${action.disabled ? "opacity-50 cursor-not-allowed" : ""}
                    `}
            >
              <div className="flex items-center">
                <span className="w-5 h-5 flex items-center justify-center mr-3 flex-shrink-0">
                  {action.icon}
                </span>
                <span className="truncate">{action.label}</span>
              </div>
              {action.subMenu && (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4 text-[var(--text-secondary)] ml-2"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </button>

            {/* Submenu */}
            {action.subMenu && activeSubMenuIndex === index && (
              <div className="absolute left-full top-0 min-w-[200px] bg-[var(--bg-surface)] dark:bg-[var(--bg-panel)] rounded-none shadow-xl border border-[var(--border-color)] dark:border-[var(--border-color)] py-1 -ml-1">
                {action.subMenu.map((subAction, subIndex) => (
                  <button
                    key={subIndex}
                    onClick={() => {
                      subAction.onClick();
                      onClose();
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-[var(--text-secondary)] dark:text-[var(--text-secondary)] hover:bg-[var(--bg-panel)] dark:hover:bg-[var(--bg-panel)] transition-colors flex items-center"
                  >
                    <span className="w-5 h-5 flex items-center justify-center mr-3 flex-shrink-0">
                      {subAction.icon}
                    </span>
                    <span className="truncate">{subAction.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </React.Fragment>
      ))}

      <style>{`
        @keyframes fade-in-up {
            from { opacity: 0; transform: translateY(5px) scale(0.95); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .animate-fade-in-up {
            animation: fade-in-up 0.1s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default ContextMenu;
