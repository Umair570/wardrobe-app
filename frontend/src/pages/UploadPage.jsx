import { useRef, useState } from 'react'
import { uploadItem, PROCESSING_STEPS } from '../api/wardrobeApi'

const TIPS = [
  'Use a plain or neutral background',
  'Ensure the clothing item is clearly visible',
  'Avoid heavily wrinkled or folded items',
  'Minimum image size: 300 x 300 px',
]

const ERROR_REASONS = [
  {
    code: 'ERR_001',
    title: 'No clothing detected',
    body: 'The AI could not find a clothing item in the uploaded image.',
  },
  {
    code: 'ERR_002',
    title: 'Unsupported image format',
    body: 'Only JPEG and PNG files are accepted. Please convert your image.',
  },
  {
    code: 'ERR_003',
    title: 'Image too blurry',
    body: 'The image quality is too low. Please use a clearer photo.',
  },
]

function ProgressRing({ percent }) {
  const r = 54
  const c = 2 * Math.PI * r
  return (
    <svg width="140" height="140" viewBox="0 0 140 140" className="mx-auto">
      <circle cx="70" cy="70" r={r} stroke="#E7E7E7" strokeWidth="6" fill="none" />
      <circle
        cx="70"
        cy="70"
        r={r}
        stroke="#111111"
        strokeWidth="6"
        fill="none"
        strokeDasharray={c}
        strokeDashoffset={c - (percent / 100) * c}
        strokeLinecap="round"
        transform="rotate(-90 70 70)"
        style={{ transition: 'stroke-dashoffset 0.4s ease' }}
      />
      <text x="70" y="66" textAnchor="middle" className="fill-ink" style={{ font: '600 22px Inter, sans-serif' }}>
        {percent}%
      </text>
      <text
        x="70"
        y="84"
        textAnchor="middle"
        className="fill-current text-soft"
        style={{ font: '500 9px "IBM Plex Mono", monospace', letterSpacing: '0.08em' }}
      >
        COMPLETE
      </text>
    </svg>
  )
}

export default function UploadPage({ onUploaded, onNavigate }) {
  const [stage, setStage] = useState('drop') // drop | selected | processing | success | error
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [stepIndex, setStepIndex] = useState(-1)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const inputRef = useRef(null)

  const reset = () => {
    setStage('drop')
    setFile(null)
    setPreviewUrl(null)
    setStepIndex(-1)
    setResult(null)
    setError(null)
  }

  const selectFile = (f) => {
    if (!f) return
    setFile(f)
    setPreviewUrl(URL.createObjectURL(f))
    setStage('selected')
  }

  const startUpload = async () => {
    setStage('processing')
    setStepIndex(-1)
    try {
      const item = await uploadItem(file, { onStep: (i) => setStepIndex(i) })
      setResult(item)
      onUploaded(item)
      setStage('success')
    } catch (err) {
      setError(err)
      setStage('error')
    }
  }

  const percent = stage === 'processing' ? Math.round(((stepIndex + 1) / PROCESSING_STEPS.length) * 100) : 0
  const remainingSeconds = Math.max(0, (PROCESSING_STEPS.length - (stepIndex + 1)) * 3)

  return (
    <div className="max-w-3xl mx-auto px-6 py-14">
      {(stage === 'drop' || stage === 'selected') && (
        <>
          <p className="eyebrow mb-3">Step 01 · Add an item</p>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-8">Upload Clothing</h1>

          <div
            onDragOver={(e) => {
              e.preventDefault()
              setIsDragOver(true)
            }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={(e) => {
              e.preventDefault()
              setIsDragOver(false)
              selectFile(e.dataTransfer.files?.[0])
            }}
            className={`relative border-2 border-dashed p-12 flex flex-col items-center text-center transition-colors
              ${isDragOver ? 'border-ink bg-panel' : 'border-ink/25'}
            `}
          >
            <input
              ref={inputRef}
              type="file"
              accept="image/png, image/jpeg"
              className="hidden"
              onChange={(e) => {
                selectFile(e.target.files?.[0])
                e.target.value = ''
              }}
            />
            <div className="placeholder-box w-16 h-16 mb-5">
              Image
              <br />
              Icon
            </div>
            <p className="font-medium mb-1.5">Drag &amp; Drop your image here</p>
            <p className="text-sm text-soft mb-5">or click the button below to choose a file</p>
            <button onClick={() => inputRef.current?.click()} className="btn-outline mb-6">
              Choose Image
            </button>
            <p className="eyebrow mb-2">Supported formats</p>
            <div className="flex gap-2">
              <span className="tag">JPEG</span>
              <span className="tag">PNG</span>
            </div>
          </div>

          <div className="panel p-5 mt-6">
            <p className="eyebrow mb-3">Tips for best results</p>
            <ul className="space-y-1.5 text-sm text-soft">
              {TIPS.map((tip) => (
                <li key={tip}>• {tip}</li>
              ))}
            </ul>
          </div>

          {stage === 'selected' && file && (
            <div className="panel p-4 mt-6 flex items-center gap-4">
              <img src={previewUrl} alt="Selected" className="w-16 h-16 object-cover placeholder-box" />
              <div className="flex-1">
                <p className="font-medium text-sm">{file.name}</p>
                <p className="text-xs text-soft">
                  {(file.size / 1024 / 1024).toFixed(1)} MB · {file.type.split('/')[1]?.toUpperCase()}
                </p>
                <p className="eyebrow text-ink/50 mt-0.5">Ready to upload</p>
              </div>
            </div>
          )}

          {stage === 'selected' && (
            <div className="flex gap-3 mt-6">
              <button onClick={startUpload} className="btn-primary flex-1">
                Upload
              </button>
              <button onClick={reset} className="btn-muted flex-1">
                Cancel
              </button>
            </div>
          )}
        </>
      )}

      {stage === 'processing' && (
        <div className="text-center">
          <p className="eyebrow mb-2">Page 3 · AI Processing</p>
          <div className="panel max-w-md mx-auto p-10 text-left">
            <ProgressRing percent={percent} />
            <h2 className="font-semibold text-center mt-4">Processing your clothing...</h2>
            <p className="text-sm text-soft text-center mb-6">Please wait while we analyze your item.</p>

            <div className="mb-2 flex items-center justify-between eyebrow">
              <span>Overall Progress</span>
              <span>
                {stepIndex + 1} / {PROCESSING_STEPS.length} steps
              </span>
            </div>
            <div className="h-1.5 bg-placeholder mb-1.5">
              <div className="h-full bg-ink transition-all duration-500" style={{ width: `${percent}%` }} />
            </div>
            <p className="text-xs text-faint mb-6">~{remainingSeconds} seconds remaining</p>

            <p className="eyebrow mb-3">Activity Log</p>
            <ul className="space-y-2.5">
              {PROCESSING_STEPS.map((step, i) => {
                const done = i <= stepIndex
                const active = i === stepIndex + 1
                return (
                  <li key={step} className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2">
                      <span
                        className={`w-4 h-4 rounded-full border flex items-center justify-center text-[10px]
                          ${done ? 'border-ink bg-ink text-white' : 'border-ink/25 text-transparent'}
                        `}
                      >
                        ✓
                      </span>
                      <span className={done ? 'text-ink' : 'text-faint'}>{step}</span>
                    </span>
                    <span className="eyebrow">{done ? 'Done' : active ? 'In progress...' : ''}</span>
                  </li>
                )
              })}
            </ul>
          </div>
        </div>
      )}

      {stage === 'success' && result && (
        <div>
          <div className="text-center mb-10">
            <div className="w-14 h-14 rounded-full border-2 border-ink flex items-center justify-center mx-auto mb-4 text-xl">
              ✓
            </div>
            <h1 className="text-2xl font-bold mb-1.5">Item Added Successfully</h1>
            <p className="text-sm text-soft">Your clothing item has been classified and saved to your wardrobe.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-5 mb-8">
            <div className="panel p-5">
              <p className="eyebrow mb-3">Preview</p>
              <img src={result.image_url} alt="" className="w-full aspect-square object-cover placeholder-box" />
            </div>
            <div className="panel p-5">
              <p className="eyebrow mb-4">Detected Details</p>
              <dl className="space-y-3 text-sm">
                {[
                  ['Category', result.name],
                  ['Color', result.color],
                  ['Confidence', `${result.confidence}%`],
                  ['Season', result.season],
                  ['Occasion', result.occasion],
                ].map(([label, value]) => (
                  <div key={label} className="flex justify-between border-b border-ink/5 pb-2">
                    <dt className="eyebrow">{label}</dt>
                    <dd className="font-medium">{value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>

          <div className="flex gap-3">
            <button onClick={() => onNavigate('wardrobe')} className="btn-primary flex-1">
              View Wardrobe
            </button>
            <button onClick={reset} className="btn-outline flex-1">
              Upload Another Item
            </button>
          </div>
        </div>
      )}

      {stage === 'error' && (
        <div>
          <div className="text-center mb-10">
            <div className="w-14 h-14 border-2 border-ink flex items-center justify-center mx-auto mb-4 text-xl">
              ⚠
            </div>
            <h1 className="text-2xl font-bold mb-1.5">Processing Failed</h1>
            <p className="text-sm text-soft">We encountered an issue while analyzing your image. See details below.</p>
          </div>

          <p className="eyebrow mb-3">Possible Reasons</p>
          <div className="space-y-3 mb-8">
            {ERROR_REASONS.map((reason) => {
              const isActive = reason.code === error?.code
              return (
                <div key={reason.code} className={`panel p-4 flex items-start gap-4 ${isActive ? 'border-ink' : ''}`}>
                  <span className="font-mono text-xs border border-ink/20 w-7 h-7 flex items-center justify-center shrink-0 mt-0.5">
                    {reason.code.slice(-2)}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-sm">{reason.title}</p>
                      {isActive && <span className="tag">Active</span>}
                    </div>
                    <p className="text-sm text-soft mt-0.5">{reason.body}</p>
                    <p className="eyebrow mt-1">{reason.code}</p>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="flex gap-3">
            <button onClick={reset} className="btn-primary flex-1">
              Upload Again
            </button>
            <button onClick={() => onNavigate('home')} className="btn-outline flex-1">
              Back Home
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
