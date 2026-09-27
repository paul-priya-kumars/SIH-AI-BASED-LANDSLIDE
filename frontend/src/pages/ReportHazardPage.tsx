import React, { useState, useRef } from 'react';
import { api } from '../services/api';
import { useGeolocation } from '../hooks/useGeolocation';
import { HazardType, SeverityLevel, HazardReport } from '../types';
import { RiskBadge } from '../components/dashboard/RiskBadge';
import {
  Camera,
  Upload,
  MapPin,
  CheckCircle2,
  AlertCircle,
  X,
  FileText,
  ShieldAlert,
  ArrowRight,
  Copy,
  ExternalLink,
} from 'lucide-react';
import { Link } from 'react-router-dom';

const HAZARD_TYPES: HazardType[] = [
  'Road crack',
  'Ground crack',
  'Rockfall',
  'Soil movement',
  'Landslide',
  'Water seepage',
  'Fallen debris',
  'Other',
];

const SEVERITY_LEVELS: { level: SeverityLevel; label: string; desc: string }[] = [
  { level: 'LOW', label: 'Low', desc: 'Minor hairline fissure or isolated moisture' },
  { level: 'MEDIUM', label: 'Medium', desc: 'Developing crack or small debris displacement' },
  { level: 'HIGH', label: 'High', desc: 'Significant subsidence, cracked road, or failing wall' },
  { level: 'CRITICAL', label: 'Critical', desc: 'Active slide, boulder blockade, or imminent structural collapse' },
];

export const ReportHazardPage: React.FC = () => {
  const { location, detectLocation, loading: geoLoading } = useGeolocation();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form State
  const [hazardType, setHazardType] = useState<string>('Road crack');
  const [description, setDescription] = useState<string>('');
  const [severity, setSeverity] = useState<SeverityLevel>('MEDIUM');
  const [latitude, setLatitude] = useState<string>(location.latitude.toString());
  const [longitude, setLongitude] = useState<string>(location.longitude.toString());
  const [locationName, setLocationName] = useState<string>(location.name || '');
  const [contactName, setContactName] = useState<string>('');
  const [contactPhone, setContactPhone] = useState<string>('');

  // Image Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  // Submission & Validation State
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [submittedReport, setSubmittedReport] = useState<HazardReport | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  // Synchronize coordinates when GPS detects new position
  React.useEffect(() => {
    setLatitude(location.latitude.toString());
    setLongitude(location.longitude.toString());
    if (location.name && !locationName) {
      setLocationName(location.name);
    }
  }, [location]);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate type
    const validExtensions = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validExtensions.includes(file.type)) {
      setValidationErrors((prev) => ({
        ...prev,
        image: 'Unsupported file format. Please upload JPG, PNG, or WEBP.',
      }));
      return;
    }

    // Validate size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      setValidationErrors((prev) => ({
        ...prev,
        image: 'Image size exceeds 10MB limit.',
      }));
      return;
    }

    setValidationErrors((prev) => {
      const rest = { ...prev };
      delete rest.image;
      return rest;
    });

    setSelectedFile(file);
    const reader = new FileReader();
    reader.onload = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const removeImage = () => {
    setSelectedFile(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!hazardType) {
      errors.hazardType = 'Please select a hazard category.';
    }

    if (!description.trim() || description.trim().length < 5) {
      errors.description = 'Please provide a descriptive explanation (at least 5 characters).';
    }

    const latNum = parseFloat(latitude);
    const lonNum = parseFloat(longitude);

    if (isNaN(latNum) || latNum < -90 || latNum > 90) {
      errors.latitude = 'Latitude must be a valid number between -90 and 90.';
    }

    if (isNaN(lonNum) || lonNum < -180 || lonNum > 180) {
      errors.longitude = 'Longitude must be a valid number between -180 and 180.';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('latitude', latitude);
      formData.append('longitude', longitude);
      formData.append('hazard_type', hazardType);
      formData.append('description', description.trim());
      formData.append('severity', severity);
      if (locationName) formData.append('location_name', locationName);
      if (contactName) formData.append('contact_name', contactName);
      if (contactPhone) formData.append('contact_phone', contactPhone);
      if (selectedFile) formData.append('image', selectedFile);

      const created = await api.createReport(formData);
      setSubmittedReport(created);
    } catch (err: any) {
      setValidationErrors((prev) => ({
        ...prev,
        submit: err.message || 'Failed to submit report. Please check connection.',
      }));
    } finally {
      setSubmitting(false);
    }
  };

  const handleCopyId = () => {
    if (!submittedReport) return;
    navigator.clipboard.writeText(submittedReport.report_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Reset form for another report
  const handleReset = () => {
    setSubmittedReport(null);
    setDescription('');
    setSelectedFile(null);
    setImagePreview(null);
    setValidationErrors({});
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs uppercase tracking-widest font-bold text-orange-400">
            Citizen Field Hazard Reporting
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
            RAPID DISPATCH
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-black text-white font-heading">
          Submit Hazard Observation
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Report road fissures, retaining wall bulging, mudflows, or loose rockfalls directly to disaster response teams.
        </p>
      </div>

      {/* SUCCESS MODAL / STATE */}
      {submittedReport ? (
        <div className="p-8 rounded-3xl glass-card border-emerald-500/40 text-center animate-in zoom-in-95 duration-200 shadow-2xl">
          <div className="w-16 h-16 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center mx-auto mb-4 text-emerald-400">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 block mb-1">
            Status: Report Submitted Successfully
          </span>
          <h2 className="text-2xl font-black text-white mb-2 font-heading">
            Observation Recorded in Disaster Registry
          </h2>
          <p className="text-xs sm:text-sm text-slate-300 max-w-md mx-auto mb-6 leading-relaxed">
            Your field report has been timestamped and queued for immediate geotechnical assessment by disaster authorities.
          </p>

          {/* Report ID Box */}
          <div className="p-4 rounded-2xl bg-slate-900 border border-slate-700 max-w-sm mx-auto mb-6 flex items-center justify-between">
            <div className="text-left">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                Tracking Identifier
              </span>
              <span className="text-lg font-mono font-black text-orange-400">
                {submittedReport.report_id}
              </span>
            </div>
            <button
              onClick={handleCopyId}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition flex items-center gap-1 text-xs"
              title="Copy tracking ID"
            >
              <Copy className="w-4 h-4" />
              <span>{copied ? 'Copied!' : 'Copy'}</span>
            </button>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              to="/reports"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-orange-600 hover:bg-orange-500 text-white font-bold text-xs rounded-xl shadow-md transition"
            >
              <FileText className="w-4 h-4" />
              <span>View In Reports History</span>
            </Link>
            <button
              onClick={handleReset}
              className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs rounded-xl border border-slate-700 transition"
            >
              Submit Another Report
            </button>
          </div>
        </div>
      ) : (
        /* REPORTING FORM */
        <form onSubmit={handleSubmit} className="p-6 sm:p-8 rounded-3xl glass-card border-slate-800 space-y-6 shadow-xl">
          {/* Top Error Alert */}
          {validationErrors.submit && (
            <div className="p-3.5 rounded-2xl bg-red-500/10 border border-red-500/30 flex items-start gap-2.5 text-xs text-red-300">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400 mt-0.5" />
              <span>{validationErrors.submit}</span>
            </div>
          )}

          {/* Section 1: Hazard Category */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-300 block mb-2.5">
              1. Hazard Classification <span className="text-red-400">*</span>
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {HAZARD_TYPES.map((type) => (
                <button
                  type="button"
                  key={type}
                  onClick={() => setHazardType(type)}
                  className={`p-3 rounded-2xl border text-xs font-semibold text-left transition flex items-center justify-between ${
                    hazardType === type
                      ? 'bg-orange-500/20 text-orange-300 border-orange-500/50 shadow-xs'
                      : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:text-slate-200 hover:border-slate-700'
                  }`}
                >
                  <span>{type}</span>
                  {hazardType === type && <CheckCircle2 className="w-3.5 h-3.5 text-orange-400" />}
                </button>
              ))}
            </div>
            {validationErrors.hazardType && (
              <span className="text-[11px] text-red-400 mt-1 block">{validationErrors.hazardType}</span>
            )}
          </div>

          {/* Section 2: Severity Assessment */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-300 block mb-2.5">
              2. Hazard Severity Assessment <span className="text-red-400">*</span>
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {SEVERITY_LEVELS.map((s) => (
                <div
                  key={s.level}
                  onClick={() => setSeverity(s.level)}
                  className={`p-3.5 rounded-2xl border cursor-pointer transition flex items-start justify-between ${
                    severity === s.level
                      ? 'bg-slate-800/90 border-orange-500/40 ring-1 ring-orange-500/20'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <RiskBadge level={s.level} size="sm" />
                    </div>
                    <p className="text-[11px] text-slate-400 leading-snug">{s.desc}</p>
                  </div>
                  <input
                    type="radio"
                    name="severity"
                    checked={severity === s.level}
                    onChange={() => setSeverity(s.level)}
                    className="mt-1 text-orange-500 focus:ring-0"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Section 3: Photograph Upload */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-300 block mb-1.5">
              3. Field Photograph (Optional but Recommended)
            </label>
            <p className="text-xs text-slate-400 mb-3">
              Upload a clear photo of the ground fissure, boulder, or slope slump (JPG, PNG, WEBP, max 10MB).
            </p>

            {imagePreview ? (
              <div className="relative rounded-2xl overflow-hidden border border-slate-700 aspect-video max-w-md bg-slate-950">
                <img
                  src={imagePreview}
                  alt="Hazard preview"
                  className="w-full h-full object-cover"
                />
                <button
                  type="button"
                  onClick={removeImage}
                  className="absolute top-2 right-2 p-1.5 rounded-full bg-slate-900/80 text-white hover:bg-red-600 transition"
                  title="Remove image"
                >
                  <X className="w-4 h-4" />
                </button>
                <div className="absolute bottom-2 left-2 px-2.5 py-1 rounded-md bg-black/70 text-[10px] text-slate-300 font-mono">
                  {selectedFile?.name} ({(selectedFile!.size / (1024 * 1024)).toFixed(2)} MB)
                </div>
              </div>
            ) : (
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-700 hover:border-orange-500/60 bg-slate-900/40 hover:bg-slate-900/70 p-6 rounded-2xl text-center cursor-pointer transition"
              >
                <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <div className="text-xs font-semibold text-slate-200">
                  Click to select photo or drag and drop
                </div>
                <div className="text-[11px] text-slate-500 mt-1 font-mono">
                  Supported formats: JPG, PNG, WEBP (Max 10MB)
                </div>
              </div>
            )}

            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleImageChange}
              className="hidden"
            />
            {validationErrors.image && (
              <span className="text-[11px] text-red-400 mt-1 block">{validationErrors.image}</span>
            )}
          </div>

          {/* Section 4: Geographic Location */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-300">
                4. Location Coordinates <span className="text-red-400">*</span>
              </label>
              <button
                type="button"
                onClick={detectLocation}
                disabled={geoLoading}
                className="text-xs text-orange-400 hover:text-orange-300 font-semibold flex items-center gap-1 transition"
              >
                <MapPin className="w-3.5 h-3.5" />
                <span>{geoLoading ? 'Detecting GPS...' : 'Auto-Capture Current GPS'}</span>
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Latitude (°N)</label>
                <input
                  type="text"
                  value={latitude}
                  onChange={(e) => setLatitude(e.target.value)}
                  placeholder="11.4102"
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white font-mono focus:border-orange-500 focus:outline-hidden"
                />
                {validationErrors.latitude && (
                  <span className="text-[10px] text-red-400 mt-1 block">{validationErrors.latitude}</span>
                )}
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Longitude (°E)</label>
                <input
                  type="text"
                  value={longitude}
                  onChange={(e) => setLongitude(e.target.value)}
                  placeholder="76.6950"
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white font-mono focus:border-orange-500 focus:outline-hidden"
                />
                {validationErrors.longitude && (
                  <span className="text-[10px] text-red-400 mt-1 block">{validationErrors.longitude}</span>
                )}
              </div>
            </div>

            <div>
              <label className="text-[11px] text-slate-400 block mb-1">
                Landmark or Sector Name (Optional)
              </label>
              <input
                type="text"
                value={locationName}
                onChange={(e) => setLocationName(e.target.value)}
                placeholder="e.g. Ooty - Coonoor Road km 14 near Valley Viewpoint"
                className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:border-orange-500 focus:outline-hidden"
              />
            </div>
          </div>

          {/* Section 5: Detailed Description */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-300 block mb-1.5">
              5. Observation Details <span className="text-red-400">*</span>
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe crack length, depth, water seepage, rock movement, or visible slope distortion..."
              className="w-full p-3.5 rounded-2xl bg-slate-900 border border-slate-700 text-sm text-white focus:border-orange-500 focus:outline-hidden leading-relaxed"
            />
            <div className="flex justify-between items-center mt-1">
              {validationErrors.description ? (
                <span className="text-[11px] text-red-400">{validationErrors.description}</span>
              ) : (
                <span className="text-[11px] text-slate-500">Provide clear observable markers</span>
              )}
              <span className="text-[11px] text-slate-500 font-mono">{description.length}/2000</span>
            </div>
          </div>

          {/* Section 6: Optional Contact Information */}
          <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
              6. Citizen Contact Information (Optional)
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <input
                  type="text"
                  value={contactName}
                  onChange={(e) => setContactName(e.target.value)}
                  placeholder="Your Name"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:border-slate-600 focus:outline-hidden"
                />
              </div>
              <div>
                <input
                  type="tel"
                  value={contactPhone}
                  onChange={(e) => setContactPhone(e.target.value)}
                  placeholder="Phone Number (+91...)"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:border-slate-600 focus:outline-hidden"
                />
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3.5 px-6 bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white font-bold text-sm rounded-2xl shadow-lg shadow-orange-600/30 transition transform active:scale-98 flex items-center justify-center gap-2"
          >
            {submitting ? (
              <>
                <div className="w-4 h-4 rounded-full border-2 border-white/20 border-t-white animate-spin" />
                <span>Encrypting & Dispatching Observation...</span>
              </>
            ) : (
              <>
                <ShieldAlert className="w-4 h-4" />
                <span>Submit Field Hazard Report</span>
              </>
            )}
          </button>
        </form>
      )}
    </div>
  );
};
