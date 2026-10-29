/** Shared semantic heading for the landing's institutional sections. */
export default function SectionHeading({ id, eyebrow, title, description, className }) {
  return (
    <div className={className}>
      <p className={eyebrow.className}>{eyebrow.text}</p>
      <h2 id={id}>{title}</h2>
      {description && <p>{description}</p>}
    </div>
  );
}
