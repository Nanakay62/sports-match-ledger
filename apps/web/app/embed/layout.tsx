export default function EmbedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="bg-paper text-ink antialiased">
      {children}
    </div>
  );
}
