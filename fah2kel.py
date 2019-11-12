import tensorflow as tf
import numpy as np
# Stop bothersome warnings!
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

fahrenheit_q = np.array([-200, -90, -40,  14, 32, 46, 59, 72, 100],  dtype=float)
kelvin_a    = np.array([144.261, 205.372, 233.15, 263.15,  273.15,  280.928, 288.15, 295.372, 310.928],  dtype=float)

l0 = tf.keras.layers.Dense(units=1, input_shape=[1])
model = tf.keras.Sequential([l0])

model.compile(loss='mean_squared_error',
              optimizer=tf.keras.optimizers.Adam(0.1))
history = model.fit(fahrenheit_q, kelvin_a, epochs=9000, verbose=False)

print("-50 (exp: 227.594)", model.predict([-50.0]))
print("0 (exp: 255.372)", model.predict([0.0]))
print("50 (exp: 283.15)", model.predict([50.0]))
print("These are the layer variables: {}".format(l0.get_weights()))
