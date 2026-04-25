import { Link } from "react-router-dom";
import type { BookWithCount } from "@/lib/api";
import { formatRelative } from "@/lib/utils";

export default function BookCard({ book }: { book: BookWithCount }) {
  return (
    <Link
      to={`/books/${book.id}`}
      className="card flex gap-3 hover:border-amber-500 transition-colors"
    >
      {book.cover_url ? (
        <img
          src={book.cover_url}
          alt=""
          className="w-16 h-24 object-cover rounded flex-shrink-0"
          loading="lazy"
        />
      ) : (
        <div className="w-16 h-24 rounded bg-ink-700 flex-shrink-0" />
      )}
      <div className="flex-1 min-w-0">
        <h3 className="font-serif text-lg truncate">{book.title}</h3>
        {book.author && <p className="text-sm text-ink-400 truncate">{book.author}</p>}
        <p className="text-xs text-ink-500 mt-2">
          {book.highlights_count} grifo{book.highlights_count === 1 ? "" : "s"} · atualizado{" "}
          {formatRelative(book.last_synced)}
        </p>
      </div>
    </Link>
  );
}
