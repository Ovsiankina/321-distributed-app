import './TagFilter.css'

interface TagFilterProps {
  tags: string[]
  selectedTag: string | null
  onSelectTag: (tag: string | null) => void
}

export function TagFilter({ tags, selectedTag, onSelectTag }: TagFilterProps) {
  return (
    <div className="tag-filter">
      <button
        type="button"
        className={selectedTag === null ? 'tag-filter-chip is-selected' : 'tag-filter-chip'}
        onClick={() => onSelectTag(null)}
      >
        Tous
      </button>
      {tags.map((tag) => (
        <button
          key={tag}
          type="button"
          className={tag === selectedTag ? 'tag-filter-chip is-selected' : 'tag-filter-chip'}
          onClick={() => onSelectTag(tag)}
        >
          {tag}
        </button>
      ))}
    </div>
  )
}
