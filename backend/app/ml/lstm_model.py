import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple, List


class LSTMModel(nn.Module):
    """LSTM股票预测模型"""

    def __init__(self, input_size: int = 5, hidden_size: int = 64, num_layers: int = 2, output_size: int = 1):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2
        )

        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, output_size)
        )

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        last_output = lstm_out[:, -1, :]
        prediction = self.fc(last_output)
        return prediction


class StockPredictor:
    """股票预测器"""

    def __init__(self, sequence_length: int = 30):
        self.sequence_length = sequence_length
        self.model = LSTMModel(input_size=5, hidden_size=64, num_layers=2)
        self.scaler = MinMaxScaler()
        self.is_trained = False

    def prepare_data(self, prices: List[float], volumes: List[int]) -> Tuple[np.ndarray, np.ndarray]:
        """准备训练数据"""
        data = np.array([[p, p, p, p, v] for p, v in zip(prices, volumes)])
        scaled_data = self.scaler.fit_transform(data)

        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i-self.sequence_length:i])
            y.append(1 if prices[i] > prices[i-1] else 0)

        return np.array(X), np.array(y)

    def train(self, prices: List[float], volumes: List[int], epochs: int = 50) -> dict:
        """训练模型"""
        X, y = self.prepare_data(prices, volumes)

        if len(X) < 10:
            return {"success": False, "message": "数据不足，需要至少40条历史数据"}

        X_tensor = torch.FloatTensor(X)
        y_tensor = torch.FloatTensor(y).unsqueeze(1)

        criterion = nn.BCEWithLogitsLoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)

        self.model.train()
        losses = []

        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = self.model(X_tensor)
            loss = criterion(outputs, y_tensor)
            loss.backward()
            optimizer.step()
            losses.append(loss.item())

        self.is_trained = True

        return {
            "success": True,
            "epochs": epochs,
            "final_loss": losses[-1],
            "samples": len(X)
        }

    def predict(self, prices: List[float], volumes: List[int]) -> dict:
        """预测股票走势"""
        if not self.is_trained:
            return {"direction": "UP", "confidence": 0.5, "predicted_price": prices[-1]}

        data = np.array([[p, p, p, p, v] for p, v in zip(prices[-self.sequence_length:], volumes[-self.sequence_length:])])
        scaled_data = self.scaler.transform(data)
        X = np.array([scaled_data])

        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X)
            output = torch.sigmoid(self.model(X_tensor)).item()

        direction = "UP" if output > 0.5 else "DOWN"
        confidence = output if output > 0.5 else 1 - output

        price_change = 0.02 if direction == "UP" else -0.02
        predicted_price = prices[-1] * (1 + price_change * confidence)

        return {
            "direction": direction,
            "confidence": round(confidence, 4),
            "predicted_price": round(predicted_price, 2)
        }
