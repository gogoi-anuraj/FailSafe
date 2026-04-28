export default function RiskBadge({ band, score }) {
  const styles = {
    HIGH  : 'badge badge-high',
    MEDIUM: 'badge badge-medium',
    LOW   : 'badge badge-low',
  }
  return (
    <span className={styles[band] || 'badge badge-low'}>
      {score !== undefined ? `${score}%` : band}
    </span>
  )
}
