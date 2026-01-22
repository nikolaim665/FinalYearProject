import { Code2, Github, Sun, Moon, Wifi, WifiOff } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { Link } from 'react-router-dom';

const Header = ({ apiStatus }) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="glass-card mx-4 mt-4 lg:mx-8 lg:mt-6">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-4 group">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl blur opacity-75 group-hover:opacity-100 transition-opacity" />
              <div className="relative p-3 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl">
                <Code2 className="w-6 h-6 text-white" />
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold gradient-text">
                QLC System
              </h1>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Questions about Learners' Code
              </p>
            </div>
          </Link>

          <div className="flex items-center gap-3">
            {/* API Status */}
            {apiStatus && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800 transition-colors">
                <div className="relative">
                  {apiStatus.status === 'healthy' ? (
                    <>
                      <Wifi className="w-4 h-4 text-emerald-500" />
                      <div className="absolute inset-0 w-4 h-4 text-emerald-500 animate-ping opacity-50">
                        <Wifi className="w-4 h-4" />
                      </div>
                    </>
                  ) : (
                    <WifiOff className="w-4 h-4 text-rose-500" />
                  )}
                </div>
                <span className={`text-sm font-medium ${
                  apiStatus.status === 'healthy'
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-rose-600 dark:text-rose-400'
                }`}>
                  {apiStatus.status === 'healthy' ? 'Connected' : 'Offline'}
                </span>
              </div>
            )}

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 transition-all duration-200 hover:scale-105"
              aria-label="Toggle theme"
            >
              {theme === 'light' ? (
                <Moon className="w-5 h-5" />
              ) : (
                <Sun className="w-5 h-5" />
              )}
            </button>

            {/* GitHub Link */}
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 transition-all duration-200 hover:scale-105"
              aria-label="View on GitHub"
            >
              <Github className="w-5 h-5" />
            </a>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
