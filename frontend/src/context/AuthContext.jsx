import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { getCurrentUser, login as requestLogin } from "../services/authService";

const TOKEN_KEY = "smartledger_access_token";
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => window.localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(Boolean(token));

  const logout = () => {
    window.localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  };

  useEffect(() => {
    const handleUnauthorized = () => logout();
    window.addEventListener("smartledger:unauthorized", handleUnauthorized);
    return () =>
      window.removeEventListener("smartledger:unauthorized", handleUnauthorized);
  }, []);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return undefined;
    }

    let active = true;
    setIsLoading(true);
    getCurrentUser()
      .then((currentUser) => {
        if (active) setUser(currentUser);
      })
      .catch(() => {
        if (active) logout();
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [token]);

  const value = useMemo(
    () => ({
      token,
      user,
      isLoading,
      isAuthenticated: Boolean(token && user),
      login: async (username, password) => {
        const result = await requestLogin(username, password);
        if (!result?.access_token) {
          throw new Error("Login response did not contain an access token");
        }
        window.localStorage.setItem(TOKEN_KEY, result.access_token);
        setToken(result.access_token);
        const currentUser = await getCurrentUser();
        setUser(currentUser);
        return currentUser;
      },
      logout,
    }),
    [isLoading, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside an AuthProvider");
  }
  return context;
}
