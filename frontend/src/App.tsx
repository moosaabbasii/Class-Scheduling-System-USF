import { Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import './App.css';
import CreateClassPage from './pages/CreateClassPage';
import { DummyPage } from './pages/DummyPage';
import { SchedulePage } from './pages/SchedulePage';
import HomePage from './pages/HomePage';
import EnrollmentPage from './pages/EnrollmentPage';
import { ApiClientProvider } from './services/ApiClientProvider';
import { CurrentUserProvider } from './services/CurrentUserProvider';
import EditClassPage from './pages/EditClassPage';
import ReportsPage from './pages/ReportsPage';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8080';

function GoBackButton() {
    const location = useLocation();
    const navigate = useNavigate();
    const isHome = location.pathname === '/';

    const handleGoBack = () => {
        if (window.history.length > 1) {
            navigate(-1);
            return;
        }
        navigate('/');
    };

    return (
        <div className="app-toolbar">
            <button disabled={isHome} onClick={handleGoBack} type="button">
                Go Back
            </button>
        </div>
    );
}

function App() {
    return (
        <ApiClientProvider baseUrl={apiBaseUrl}>
            <CurrentUserProvider>
                <div className="app-layout">
                    <GoBackButton />
                    <main className="main-content">
                        <Routes>
                            <Route element={<HomePage />} path="/" />
                            <Route element={<SchedulePage />} path="/schedules/:scheduleId" />
                            <Route element={<EditClassPage />} path="/schedules/:scheduleId/classes/:classId" />
                            <Route element={<CreateClassPage />} path="/schedules/:scheduleId/create-class" />
                            {/* US5: Enrollment comparison page */}
                            <Route element={<EnrollmentPage />} path="/enrollment" />
                            <Route
                                element={
                                    <DummyPage
                                        description="Manage and map instructor assignments."
                                        sections={[
                                            {
                                                title: 'Directory',
                                                text: 'Instructor list, availability, and qualifications.',
                                            },
                                            {
                                                title: 'Assignment Rules',
                                                text: 'Policies for balancing teaching load.',
                                            },
                                        ]}
                                        title="Instructors"
                                    />
                                }
                                path="/instructors"
                            />
                            <Route element={<ReportsPage />} path="/reports" />
                            <Route
                                element={
                                    <DummyPage
                                        description="The requested page does not exist."
                                        sections={[
                                            {
                                                title: 'Tip',
                                                text: 'Use the back button to return to the previous page.',
                                            },
                                        ]}
                                        title="Not Found"
                                    />
                                }
                                path="*"
                            />
                        </Routes>
                    </main>
                </div>
            </CurrentUserProvider>
        </ApiClientProvider>
    );
}

export default App;
