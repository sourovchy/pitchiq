import { createBrowserRouter } from "react-router";

import { MatchAnalysisPage } from "../features/match-analysis/MatchAnalysisPage";
import { AppLayout } from "../layouts/AppLayout";
import { HomePage } from "../pages/HomePage";
import { NotFoundPage } from "../pages/NotFoundPage";

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "analysis", element: <MatchAnalysisPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);

