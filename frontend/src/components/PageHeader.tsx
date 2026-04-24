type PageHeaderProps = {
    title: string;
    eyebrow?: string;
    subtitle?: string;
    children?: React.ReactNode;
};

export function PageHeader({
    subtitle,
    title = 'Class Scheduling Console',
    eyebrow = 'Bellini College',
    children,
}: PageHeaderProps) {
    return (
        <header className="page-header">
            <p className="eyebrow">{eyebrow}</p>
            <h1>{title}</h1>
            <p className="subtitle">{subtitle}</p>
            {children}
        </header>
    );
}
