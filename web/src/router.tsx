import { createBrowserRouter } from "react-router-dom";
import App from "./App";
import Home from "./pages/Home";
import Review from "./pages/Review";
import Library from "./pages/Library";
import BookDetail from "./pages/BookDetail";
import Tags from "./pages/Tags";
import TagFeed from "./pages/TagFeed";
import Settings from "./pages/Settings";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <Home /> },
      { path: "review", element: <Review /> },
      { path: "library", element: <Library /> },
      { path: "books/:id", element: <BookDetail /> },
      { path: "tags", element: <Tags /> },
      { path: "tags/:name", element: <TagFeed /> },
      { path: "settings", element: <Settings /> },
    ],
  },
]);
