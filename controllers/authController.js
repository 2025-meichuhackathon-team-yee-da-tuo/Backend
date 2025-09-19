const User = require('../models/User');
const bcrypt = require('bcryptjs');

exports.register = async (req, res) => {
  const { email, password, confirmPassword } = req.body;

  if (password !== confirmPassword) {
    return res.json({ code: 3 }); 
  }

  if (password.length < 8) {
    return res.json({ code: 2 });
  }

  try {
    let user = await User.findOne({ email });

    if (user) {
      return res.json({ code: 1 }); 
    }

    user = new User({
      email,
      password
    });

    const salt = await bcrypt.genSalt(10);
    user.password = await bcrypt.hash(password, salt);

    await user.save();

    res.json({ code: 0 }); 
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
};

exports.login = async (req, res) => {
  const { email, password } = req.body;

  try {
    let user = await User.findOne({ email });

    if (!user) {
      return res.json({ code: 1 }); 
    }

    const isMatch = await bcrypt.compare(password, user.password);

    if (!isMatch) {
      return res.json({ code: 1 }); 
    }

    res.json({ code: 0 }); 
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
};
