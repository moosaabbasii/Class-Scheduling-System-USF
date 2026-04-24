type DummyPageProps = {
    description: string;
    sections: {
        text: string;
        title: string;
    }[];
    title: string;
};

export function DummyPage({ description, sections, title }: DummyPageProps) {
    return (
        <div className="app-shell">
            <section className="page-header">
                <p className="eyebrow">Placeholder</p>
                <h1>{title}</h1>
                <p className="subtitle">{description}</p>
            </section>

            <section className="dummy-grid">
                {sections.map((section) => (
                    <article className="dummy-card" key={section.title}>
                        <h2>{section.title}</h2>
                        <p>{section.text}</p>
                    </article>
                ))}
            </section>
        </div>
    );
}
