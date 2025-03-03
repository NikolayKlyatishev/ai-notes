import GoogleIcon from '@mui/icons-material/Google';
import {
    Alert,
    Box,
    Button,
    Container,
    Divider,
    Paper,
    Typography
} from '@mui/material';
import React, { useState } from 'react';
import { API_BASE_URL, API_ENDPOINTS } from '../config';

const Login: React.FC = () => {
    const [error, setError] = useState<string | null>(null);

    const handleGoogleLogin = () => {
        window.location.href = `${API_BASE_URL}${API_ENDPOINTS.AUTH.LOGIN_GOOGLE}`;
    };

    const handleYandexLogin = () => {
        window.location.href = `${API_BASE_URL}${API_ENDPOINTS.AUTH.LOGIN_YANDEX}`;
    };

    return (
        <Container maxWidth="sm">
            <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
                    <Typography component="h1" variant="h5" align="center" gutterBottom>
                        Вход в AI Notes
                    </Typography>

                    {error && (
                        <Alert severity="error" sx={{ mb: 2 }}>
                            {error}
                        </Alert>
                    )}

                    <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <Button
                            fullWidth
                            variant="contained"
                            color="primary"
                            startIcon={<GoogleIcon />}
                            onClick={handleGoogleLogin}
                            sx={{ py: 1.5 }}
                        >
                            Войти через Google
                        </Button>

                        <Button
                            fullWidth
                            variant="contained"
                            color="warning"
                            onClick={handleYandexLogin}
                            sx={{ py: 1.5 }}
                        >
                            Войти через Яндекс
                        </Button>

                        <Divider sx={{ my: 2 }}>
                            <Typography variant="body2" color="text.secondary">
                                или
                            </Typography>
                        </Divider>

                        <Typography variant="body2" color="text.secondary" align="center">
                            Для входа используйте ваш аккаунт Google или Яндекс.
                            Это обеспечивает безопасную аутентификацию без необходимости создавать отдельный пароль.
                        </Typography>
                    </Box>
                </Paper>
            </Box>
        </Container>
    );
};

export default Login; 