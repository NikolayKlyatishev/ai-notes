import YandexIcon from '@mui/icons-material/EmojiEmotions';
import GoogleIcon from '@mui/icons-material/Google';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import {
    Alert,
    Avatar,
    Box,
    Button,
    Container,
    Divider,
    Paper,
    Typography,
    useTheme
} from '@mui/material';
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Login: React.FC = () => {
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const theme = useTheme();
    const { isAuthenticated } = useAuth();

    useEffect(() => {
        if (isAuthenticated) {
            navigate('/');
        }
    }, [isAuthenticated, navigate]);

    const handleGoogleLogin = () => {
        setLoading(true);
        setError(null);
        try {
            window.open('http://localhost:8080/api/auth/login/google', '_blank');
            setLoading(false);
        } catch (err) {
            console.error('Ошибка при переходе на страницу авторизации Google:', err);
            setError('Не удалось перейти на страницу авторизации Google');
            setLoading(false);
        }
    };

    const handleYandexLogin = () => {
        setLoading(true);
        setError(null);
        try {
            window.open('http://localhost:8080/api/auth/login/yandex', '_blank');
            setLoading(false);
        } catch (err) {
            console.error('Ошибка при переходе на страницу авторизации Яндекс:', err);
            setError('Не удалось перейти на страницу авторизации Яндекс');
            setLoading(false);
        }
    };

    return (
        <Container maxWidth="sm">
            <Box sx={{
                mt: 8,
                mb: 8,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center'
            }}>
                <Avatar sx={{
                    m: 1,
                    bgcolor: 'primary.main',
                    width: 56,
                    height: 56,
                }}>
                    <LockOutlinedIcon fontSize="large" />
                </Avatar>

                <Typography component="h1" variant="h4" align="center" gutterBottom sx={{ fontWeight: 'bold', mb: 3 }}>
                    Вход в AI Notes
                </Typography>

                <Paper
                    elevation={3}
                    sx={{
                        p: 4,
                        width: '100%',
                        borderRadius: 2,
                        background: `linear-gradient(145deg, ${theme.palette.background.paper}, ${theme.palette.grey[100]})`,
                    }}
                >
                    {error && (
                        <Alert severity="error" sx={{ mb: 3 }}>
                            {error}
                        </Alert>
                    )}

                    <Typography variant="body1" paragraph align="center" sx={{ mb: 4 }}>
                        Выберите способ входа в систему:
                    </Typography>

                    <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <Button
                            fullWidth
                            variant="contained"
                            color="primary"
                            startIcon={<GoogleIcon />}
                            onClick={handleGoogleLogin}
                            sx={{
                                py: 1.5,
                                fontSize: '1rem',
                                borderRadius: 8,
                                boxShadow: 3,
                                transition: 'all 0.2s',
                                '&:hover': {
                                    transform: 'translateY(-2px)',
                                    boxShadow: 6,
                                }
                            }}
                        >
                            Войти через Google
                        </Button>

                        <Button
                            fullWidth
                            variant="contained"
                            color="warning"
                            startIcon={<YandexIcon />}
                            onClick={handleYandexLogin}
                            sx={{
                                py: 1.5,
                                fontSize: '1rem',
                                borderRadius: 8,
                                boxShadow: 3,
                                transition: 'all 0.2s',
                                '&:hover': {
                                    transform: 'translateY(-2px)',
                                    boxShadow: 6,
                                }
                            }}
                        >
                            Войти через Яндекс
                        </Button>
                    </Box>

                    <Divider sx={{ my: 4 }}>
                        <Typography variant="body2" color="text.secondary">
                            Безопасная аутентификация
                        </Typography>
                    </Divider>

                    <Typography variant="body2" color="text.secondary" align="center" sx={{ px: 2 }}>
                        Для входа используйте ваш аккаунт Google или Яндекс.
                        Это обеспечивает безопасную аутентификацию без необходимости создавать отдельный пароль и хранить его в нашей системе.
                    </Typography>
                </Paper>

                <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 4 }}>
                    © {new Date().getFullYear()} AI Notes. Все права защищены.
                </Typography>
            </Box>
        </Container>
    );
};

export default Login; 