import BackLink from '../components/BackLink'

export default function ItemDetailsPage({ item, onBack, onVisualize, onAskStylist, onRemove }) {
  if (!item) return null

  return (
    <div className="max-w-4xl mx-auto px-6 py-14">
      <BackLink onClick={onBack} />
      <h1 className="text-2xl font-bold mb-8">Clothing Details</h1>

      <div className="grid md:grid-cols-2 gap-8">
        <div>
          <div className="aspect-square w-full mb-3 rounded-2xl overflow-hidden bg-ink/5 border border-ink/10 flex items-center justify-center p-4">
            {item.image_url ? (
              <img src={item.image_url} alt={item.name} className="w-full h-full object-contain" />
            ) : (
              <span className="text-soft text-sm">No Image</span>
            )}
          </div>
        </div>


        <div>
          <p className="eyebrow mb-2">Category</p>
          <h2 className="text-2xl font-bold mb-5">{item.name}</h2>

          <div className="panel mb-5">
            <p className="eyebrow px-4 pt-4 pb-2">Item Information</p>
            <dl className="text-sm">
              {[
                ['Color', item.color],
                ['Material', item.material],
                ['Season', item.season],
                ['Occasion', item.occasion],
                ['Added', item.addedDate],
                ['Confidence', `${item.confidence}%`],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between px-4 py-2.5 border-t border-ink/10">
                  <dt className="text-soft">{label}</dt>
                  <dd className="font-medium">{value}</dd>
                </div>
              ))}
            </dl>
          </div>

          <p className="eyebrow mb-3">Actions</p>
          <p className="text-xs text-soft mb-3">
            For a full outfit preview, go to Wardrobe and select a top, bottom, and shoes.
          </p>
          <div className="flex flex-col gap-2.5">
            <button onClick={() => onVisualize(item)} className="btn-outline">
              Preview This Item
            </button>
            <button onClick={() => onAskStylist(item)} className="btn-outline">
              Ask AI Stylist
            </button>
            <button onClick={() => onRemove(item)} className="btn-muted">
              Remove Item
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
